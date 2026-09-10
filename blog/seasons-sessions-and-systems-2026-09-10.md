---
slug: seasons-sessions-and-systems
title: "Seasons, Sessions, and Systems"
date: 2026-09-10
authors: [vladislav]
tags: [process, design, development]
draft: true
---

# Seasons, Sessions, and Systems

I keep finding the same shape of work in three places that initially seem to
have little to do with one another: developing software, playing a seasonal
action RPG, and composing and producing music.

They are not the same activity, and the analogy has limits. A game character is
allowed to be temporary. A recording eventually becomes fixed. Software has to
remain understandable to people who were not present for its first version.
But all three involve guiding a developing thing towards a destination while
working with incomplete information, limited resources, and an accumulating
history of choices.

The shared skill is not having the perfect plan at the beginning. It is making
the next worthwhile change without losing the shape of the whole.

## A Build Is Also a Progression Plan

A seasonal ARPG build can have a very clear end state: a final skill setup, a
passive tree, an item configuration, perhaps a specific interaction that makes
the build work. Looking only at that end state can make the problem appear
simple. Find the items, take the nodes, equip the skills, finish the build.

Playing the character is different. The route has to account for random drops,
the cost and availability of upgrades, the changing power curve of skills and
items, and the content the character needs to clear at each stage. The skill
that is best at level twenty may not be the intended endgame skill. It may be
correct to use it anyway because it makes the next several hours smoother and
gets the character to the point where the eventual build is practical.

At every stage, the question is not simply “what is the best item?” It is more
like this:

> What is the next upgrade with the best return for its cost, given what I have
> now, while keeping the eventual build reachable?

That question has three parts. An upgrade must offer enough immediate power to
matter. It must be affordable in currency, time, and attention. And it must not
steer the character so far from its direction that today's shortcut becomes
tomorrow's expensive rebuild.

There is a real tension here. Following an endgame guide too literally can make
the levelling experience weak and frustrating. Chasing every powerful drop can
produce a character that has no coherent path once those temporary advantages
stop carrying it. Good progression holds both facts at once: the final design
matters, and the current state is real.

## Software Has the Same Middle Game

Software projects also have destinations: a language model, an architecture, a
product capability, or a reliability property that the system should eventually
have. Those are necessary. Without them, local decisions have no direction.

They are not enough to tell us what to do next.

The next software change has to fit the codebase and the team that exist today.
It has to account for what is known, what is still uncertain, what can be
tested, and what future work it enables or forecloses. A small adapter, a
temporary representation, or a deliberately narrow implementation can be the
right move if it creates a useful feedback loop and leaves a clear route to the
intended model.

The important word is *deliberately*. A levelling skill is not technical debt
merely because it is temporary. It becomes debt when nobody knows it is
temporary, when its replacement path is absent, or when it quietly dictates the
rest of the build. The same applies to software. A transitional design needs a
job, a boundary, and a reason it can later be removed.

This is one reason I care about RFCs, specifications, fixtures, and explicit
roadmaps in Metel. They do not make development predictable in the sense of
making every intermediate decision obvious. They make the intended direction
visible, so a local decision can be evaluated against it. They let me ask
whether a change is a good progression step rather than merely a locally
convenient patch.

## Composition and Software Are Both Designed in Layers

The musical parallel is different. A finished piece is usually understood at
several levels of abstraction at once. There may be an emotional or dramatic
arc, a harmonic language, melodic and rhythmic ideas, a form, an arrangement,
individual performances, sound choices, and finally a mix. None is merely a
later cosmetic pass over the others. Each shapes what the piece can become.

A compelling motif cannot compensate for a form that never develops it. A
careful arrangement cannot solve harmony that does not support the intended
movement. A strong composition can also fail to communicate if the production
buries its important relationships. Conversely, a sound choice can suggest a
new arrangement, and an arrangement can reveal that a musical idea needs to
change. The design moves between layers, repeatedly checking whether they still
say the same thing.

A technically demanding performance or composition can be genuinely impressive,
and deserves respect on those terms alone. Technical achievement is part of the
work's meaning for many listeners and musicians. But it is not, by itself, a
complete account of whether a piece is good — a necessarily subjective judgment.
Virtuosity, density, and complexity can serve an emotional idea, a groove, a
form, or a particular sonic world; they can also obscure them. The point is not
that simpler music is better, but that technique is one design layer among
several rather than a substitute for all the others.

Software has the same property. A final system is not just source code. It has a
purpose and user-facing behaviour; a conceptual model; invariants and safety
rules; module and API boundaries; data representations; algorithms; concrete
code; tests; and operational behaviour. These are different descriptions of one
thing, not a stack where only the bottom layer is real.

The parallel with virtuosity is deliberate. Clever algorithms, elaborate type
machinery, and exceptionally clean local code can be real technical
achievements, and can be worth valuing in their own right. They are still not a
complete measure of whether software is good. A system also has to serve its
purpose, remain coherent as it changes, make its behaviour understandable, and
be reliable for the people who depend on it. As with music, technical complexity
can support the whole or distract from what the whole is trying to do.

That matters because a failure can originate at any layer. A beautifully written
function cannot repair a confused domain model. A well-chosen data structure
cannot establish an API contract nobody has specified. A clear specification is
not enough if the implementation or tests no longer embody it. Equally, local
implementation constraints sometimes expose a flaw in a high-level idea and
should feed back into the design rather than being treated as an inconvenience.

This is why I treat RFCs, specifications, formal rules, fixtures, and code as a
connected body of work in Metel. They describe the language at different levels
of abstraction, and they need to change together. The aim is not for every
detail to be decided at the top before implementation begins. It is for each
level to make its part of the design explicit enough that the others can be
checked against it.

## Progression Integrity

I think of the common principle as *progression integrity*. Each step should do
enough useful work now while preserving the ability to make the next good step
later.

That rules out two tempting extremes. The first is trying to build the final
thing immediately: using an endgame skill before it has the support it needs,
introducing a complete abstraction before the surrounding system can exercise
it, or polishing a recording before its arrangement exists. The second is
chasing whatever is strongest or easiest in the moment until the work has no
coherent destination.

Neither extreme is really pragmatic. The first mistakes a plan for a route. The
second mistakes movement for progress.

The better question is smaller and harder: what is the best next upgrade for
this state of the work? Answering it requires a destination, an honest picture
of the present, and enough structure to understand the cost of changing course.
That is true whether the work is a character in a three-month league or a
language that still has years of changes ahead of it. A piece of music adds the
companion discipline: keep the design coherent across every level at which the
finished work can be understood.

## Where the Analogy Stops

There is one difference worth keeping in view. Software decisions often become
other people's environment: collaborators, users, maintainers, and downstream
tools inherit them. That gives software a responsibility that a private game
build usually does not have.

So the lesson is not to treat software as a game, or to make every development
choice provisional. It is to treat plans as guides rather than scripts, and to
treat temporary steps as first-class design objects. Name them, give them a
purpose, keep their replacement path visible, and revisit them when the state
of the work changes.

That is how a series of local decisions becomes a coherent thing rather than a
collection of lucky drops.
