---
slug: how-metel-is-designed
title: "How Metel Is Designed"
date: 2026-09-09
authors: [vladislav]
tags: [process, language-design, metel]
draft: true
---

# How Metel Is Designed

The things that matter most in a piece of software are rarely the result of a
sudden brilliant idea, or of writing good code alone. Reliability, coherence,
long-term maintainability, and the ability to change course all come from
structure and process.

That can sound disappointingly bureaucratic. It should not. A process is not a
substitute for judgment; it is a way to make judgment survive contact with a
large, changing system. It records a decision, gives it a place to be challenged,
and makes sure its consequences are checked before they become expensive.

## Good Code Is Not Yet Good Software

I have seen brilliant people write horrible code, and people who write beautiful
code produce horrible software. Neither observation is a verdict on their
ability. Code can be clever, fast, elegant, and locally correct while the system
around it is fragile, contradictory, or impossible to change safely.

Most of the failures that matter sit a layer above the code itself. Does the
feature have a precise meaning? Does it agree with the features that already
exist? Can a reader tell whether it is implemented, merely planned, or already
superseded? When its spelling changes, will the examples that teach it change as
well? When a new edge case appears, is there a place to record it and a route to
revisit the earlier decision?

Those are design and maintenance questions. A compiler can help check an
implementation, but it cannot decide that two separately sensible language
features make each other incoherent. Formatting and tests can make a codebase
more dependable, but they cannot make an undocumented decision discoverable.

For a language project, this matters unusually early. A small rule about a
reference, a closure, or a record can quietly constrain every feature that comes
after it. The code may still be small when that happens. The cost of changing the
idea is not.

## The Process Is Part Of The Design

Metel uses RFCs to give a design decision a life beyond the moment it was
proposed. An RFC is not just a document that says “we should do this.” It is a
place to explain the problem, choose among alternatives, state the invariants,
and leave a trail for the person who has to change the design later — which may
well be me after I have forgotten why the first choice looked obvious.

The lifecycle is deliberately simple:

```text
draft → under review → accepted → integrated → implemented
```

A proposal can also be superseded or refused from any stage. That is not a
failure of the process. It is one of its intended outputs. A language that cannot
say “this was the wrong direction” accumulates accidental commitments until it
cannot move.

The important stage is **integrated**. Acceptance says that a proposal is
settled on its own terms. Integration asks a harder question: does it still make
sense when combined with the rest of the language, including related work that
is still in flight?

At that stage, the proposal is merged into the specification and tested with
worked examples that cross feature boundaries. The goal is not to repeat the
happy-path example from the RFC. It is to look for the program that makes two
rules disagree: a partial move through a structured value, a borrow that crosses
an abstraction boundary, a generic constraint that changes what an operation is
allowed to do.

That distinction came from experience. An earlier allocator and region cluster
contained proposals that each made sense in isolation, but whose assumptions no
longer fit together once a value could outlive one part of the model while its
storage remained alive in another. Catching that later meant revisiting several
accepted RFCs at once. The lesson was not “never accept a proposal.” It was that
acceptance is not the last useful question to ask.

The [RFC process](/docs/rfcs/rfc-process) describes the lifecycle and its exit
criteria in detail. The short version is that a decision is not ready for code
merely because it reads well in a document. It needs to survive the rest of the
system.

## Documentation Is Part Of The System

In Metel, documentation is interlinked with the code rather than written after
the fact. An RFC names the design decision; the specification gives that decision
its public, normative form; implementation tracking records whether the
interpreter has caught up; tests and worked examples exercise the behaviour; and
release notes tell readers when it became available. Each is incomplete without
the others.

That relationship makes documentation production and maintenance explicit parts
of the work. An implementation is not finished just because its tests pass. If it
changes a user-facing rule, its specification, examples, and release notes need
to change with it. If an RFC reaches the integrated stage, it needs a linked
implementation task and availability markers in the relevant specification
sections. These are not optional announcements attached to the real work; they
are the connections that let a future change be understood and made safely.

Detailed documentation also keeps the language changeable. It means a change can
start from an account of the current behaviour — its rules, examples, rationale,
and known interactions — instead of requiring someone to reconstruct the
language's overall behaviour after every edit. That record does not make change
free, but it makes the consequences of change visible before they become bugs.

## One Chain From Design To Evidence

For Metel, the documents and tests are not a trail of loosely related artefacts.
They are one body of evidence about what the language means:

```text
RFC design → specification → formal rules → executable fixtures
```

An RFC records the problem, the alternatives, and the decision. The specification
turns that decision into the current public account of the language; it is the
place a reader should go to learn what is true now, rather than reconstructing it
from a sequence of historical proposals. Formal legality and dynamic-semantics
rules make the parts of that account that need precision explicit and stable
enough to cite. Fixtures then run real programs that demonstrate the stated
behaviour, including rejected programs and feature interactions.

The links run in both directions. A fixture can point to the exact formal rule it
exercises; an integrated RFC can point to the specification rules it establishes;
and a reader of the specification can follow a rule to executable examples. If a
rule changes, its fixtures are not merely regression tests that happen to fail:
they are part of the evidence that the changed rule still says what the
implementation does. If an interaction cannot be expressed in the specification
or tested by a fixture, that is a design question to resolve, not paperwork to
defer.

The fixture corpus also runs in automated CI. That makes these checks part of
the ordinary cost of changing the language, rather than a manual audit someone
has to remember to perform before a release.

This is why Metel has formal rules and fixtures alongside explanatory prose. The
prose makes the language teachable; the rules make important claims precise; the
fixtures make those claims executable. None is a complete definition alone.

## Keep The Public Story True

Process also reaches beyond implementation. A language is partly made of the
examples, specifications, release notes, and tutorials that tell people how to
use it. If those teach syntax that no longer parses, they are not harmlessly out
of date; they are a broken interface.

That is why an RFC that changes existing syntax must also sweep the prose that
uses it, and why examples need to be compiled rather than only reread. It is also
why the specification distinguishes a released feature from a planned one at the
point where a reader encounters it. The implementation, the specification, and
the teaching material are different views of the same language. Letting them
drift apart creates work for everyone who comes next.

This is unglamorous work. It is also the work that makes future changes possible.
An accurate map of the system lets a change begin with understanding instead of
archaeology.

## Why Start With A Detailed Specification

Not every language has a specification this detailed, and producing one is a
large, ongoing investment. Rust is a useful reminder of that. Rust 1.0 shipped
in 2015, and the [Rust Reference](https://doc.rust-lang.org/reference/) has long
been its primary technical reference, but Rust's own documentation distinguishes
the Reference from a formal specification. The effort to create an official
specification began with an [RFC submitted in 2022 and accepted in
2023](https://rustfoundation.org/media/ferrous-systems-donates-ferrocene-language-specification-to-rust-project/);
in 2025, the Rust Project [adopted the existing Ferrocene Language
Specification](https://blog.rust-lang.org/2025/03/26/adopting-the-fls/) as part
of that work. It is an important, ongoing formalization effort, not a claim that
Rust lacked careful documentation before it.

Metel is choosing to build its detailed specification early. That is not because
the project is already large enough to require institutional ceremony. It is
because I have a full-time job and other projects, so I cannot rely on continuous
context or on remembering every conclusion for years. The specification, its
formal rules, and the fixture corpus are durable working memory. They let me
return to a design, make a change deliberately, and verify the result without
reconstructing the entire language each time.

## Structure Creates Room For Judgment

None of this turns language design into a mechanical procedure. It cannot tell
me whether a feature is worth its complexity, whether a spelling feels natural,
or whether Metel's particular combination of ideas is a useful one. Those remain
judgment calls.

What structure can do is make those calls explicit, test their consequences, and
leave them open to revision. It replaces “I think this is fine” with a design
that has examples, a stated status, known interactions, and a route back when
new evidence arrives.

AI-heavy development is not different from hand-written development in this
respect. It can change the speed of producing code, but it does not supply the
structure that keeps a project coherent over time. A structured approach is how
long-term goals become achievable — in software, and in the rest of life too.

Even if agents wrote every line of Metel's implementation, the central work
would remain:

- **Language design:** deciding which problems matter, what rules mean, and
  which tradeoffs are acceptable.
- **Research:** finding prior art, understanding its assumptions, and separating
  a useful analogy from a design that actually fits Metel.
- **Process shaping:** defining the checks, decision records, and revision paths
  that keep independent changes from drifting apart.
- **Planning:** keeping a long-term direction while choosing the next small piece
  of work that makes the rest safer or easier.
- **Quality assurance:** designing adversarial examples, checking feature
  interactions, testing the public behaviour, and deciding what “done” means.
- **Documentation and review:** maintaining the shared account of the language,
  then asking whether the implementation, specification, examples, and releases
  still agree.

Agents can contribute to every item on that list. They do not make the list go
away, and they do not remove the need to decide what good work looks like.

That is the kind of reliability I want Metel to have. Not the appearance of a
finished language, and not a pile of individually impressive features, but a
project that can keep learning without losing track of what it has learned.
