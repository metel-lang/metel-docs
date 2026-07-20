---
id: strategic-overview-2026-07-20
title: "Language Design — Strategic Overview"
type: report
created_date: '2026-07-20'
---

# Language Design — Strategic Overview

*This document supersedes `strategic-overview-2026-07-15.md` as the dated narrative
record. For the living priorities/triggers document both this and every prior cycle
write back to, see `OBJECTIVES.md`.*

*This cycle carries a specific new ask, not just a routine refresh: read
`public/blog/introducing-metel-2026-07-15.md` ("Introducing Metel") as **real
strategic intent**, not marketing copy, and cross-reference it against what
`OBJECTIVES.md` and the RFC corpus actually say and actually contain. That
cross-reference is this document's main contribution — the RFC-corpus survey below
it is more routine, matching the shape of prior cycles.*

---

## Blog Post as Strategic Intent — Cross-Reference Against `OBJECTIVES.md`

"Introducing Metel" is the project's first public strategic statement — written,
revised, and re-revised across most of a single session (this one), including changes
landing today, the same day this overview is written. Read as intent rather than copy,
it holds up well in three places and diverges in two. Both are worth naming plainly.

### Where it matches internal reality closely — this is real alignment, not spin

**The substrate reframing is near-verbatim the same claim in both places.** The blog:
"Allocators were the first piece I built, but they turned out to be just the first use
case of a broader substrate — structural shape, field-sensitive ownership, brand-like
identity, lifetimes named after real bindings." `OBJECTIVES.md` §1 (written 07-15, the
same day, independently of the blog): "A systems language whose public face is
allocator-aware storage and resource control, but whose real semantic substrate is
lower-level: structural shape, per-field multiplicity, brand identity/provenance, and
binding-named lifetime validity." These are the same sentence in two registers. That's
a genuinely good sign — the public narrative isn't diverging from the internal
strategic document, it's restating it accurately for a different audience.

**Records' elevation matches Priority 2 exactly.** The blog calls records "the piece I
currently find most worth pursuing" and "the closest Metel gets to a genuinely open
problem." `OBJECTIVES.md` Priority 2 independently calls structural types/records "now
the main medium-term design priority" and Trigger 6 tracks the live RFC-0089/RFC-0090
dependency tension around exactly this. Matched.

**The hedging on comptime/linear-types/effects is honest, not just cautious phrasing.**
The blog says comptime is "still draft and deferred," and that linear types/effects'
"open question... is whether they belong in Metel at all." That's the same posture
`OBJECTIVES.md` Priority 4 and the roadmap's Stage B/C gating take internally — most
project-announcement posts oversell unshipped features; this one, if anything,
undersells them. Worth noting as a positive finding, not assumed.

### Where it diverges from internal reality

**1. The "Foundation: Allocators And Lifetimes" section shows unimplemented syntax with
no disclaimer, inconsistent with the post's own standard elsewhere.** Verified directly
against `metel-interpreter/src/`: `grep -rn '"@"' src/grammar.pest` finds exactly one
use of `@`, in `native_attr` (`native(@std.core...)`, the Rust-FFI annotation for
stdlib functions) — nothing resembling an allocator-pointer type. There is no named
lifetime-anchor return syntax (`&x T`) anywhere in the grammar or typechecker either.
`@Heap User { name: "Ada" }` and `fun first(x: &Str, y: &Str) -> &x Str` are 0%
implemented — confirmed both by this direct grep and independently by
`reports/implementation/roadmap-2026-07-07.md`'s own L2 row ("`grep` for
`allocator`/`region`/`lifetime`/`linear`/`affine` across `src/` returns nothing
relevant"), still true today. That's not wrong to show — these are real, accepted
RFCs — but the **Records** section, showing equally unimplemented `ToRecord`/
`FromRecord` code, explicitly says "This is a design sketch, not executable Metel." The
Foundation section's code blocks get no equivalent caveat, right next to "What Already
Exists," whose code block *is* runnable (verified by actually running it against
`target/release/metel` earlier this session). A reader skimming code blocks alone would
reasonably conclude allocator/lifetime syntax already works. Recommend adding the same
disclaimer sentence to the Foundation section that Records already has — a small,
mechanical fix, not evaluated further here since fixing it wasn't this turn's ask.

**2. This week's actual RFC-writing effort went somewhere the blog doesn't mention and
the priorities document ranks below both records and the allocator cluster.** Four new
RFCs opened in the last four days — RFC-0107 (07-17), RFC-0108 (07-17), RFC-0109
(07-18), RFC-0110 (07-20, today) — all in one tight cluster extending RFC-0067a's
(already-implemented) auto-deref into places it doesn't yet reach: matching a `&T`
directly in `match`, destructuring through a reference, disambiguating whether `p = v`
means write-through or rebind. That's real, well-executed design work — but it's
surface-ergonomics polish on an already-shipped mechanism, not the substrate work
either the blog or `OBJECTIVES.md` Priority 2 names as the actual medium-term
priority (records/per-field ownership: RFC-0089/0090, untouched this window) or the
fully-ratified-since-07-10, still-0%-implemented allocator/lifetime cluster
(RFC-0063/65/66/67/68/73/77 — Priority 1's own unfinished follow-through). This is a
concrete instance of the standing meta-risk `OBJECTIVES.md` §1 exists to watch for,
just not the exact shape it was written to catch (that section watches for
already-settled work sitting idle while *new* design keeps happening; this is the
mirror case — a third, lower-ranked area got the attention while both higher-ranked
areas sat still). Named here rather than left implicit — see the new trigger below.

---

## RFC Corpus — State As Of Today

**109 RFCs total** (from `internal/rfcs/REGISTRY.md`, the generated/authoritative
count): 33 draft, 3 under-review, 9 accepted, 0 integrated, 38 implemented, 12
superseded, 14 refused. `rfc.py check` and `index --check-drift` both report clean.

**Verified against source, not just frontmatter**, the real shipped surface: aspect
coherence (orphan rule, overlap, negative impls — real logic in `coherence.rs`,
backing RFC-0060/0072/0081), associated types (RFC-0082, across
`typechecker/{conversions,inference,mod}.rs`), structural aspect bounds (RFC-0061),
conditional impls (RFC-0036), return-position `impl Aspect` (RFC-0037), `&T`/`&mut T`
with auto-deref (RFC-0067a), bottom type `!` (RFC-0078), the module system, `List<T>`
and fixed arrays, string interpolation, closures, `var` bindings, and the `extend`/
`public`/`var` surface renames (RFC-0098). Confirmed **absent**, consistent with draft
status: `Linear`/multiplicity types (RFC-0089/0091), `comptime` (RFC-0092/0094), and
user-facing `Rc<T>`/`Arc<T>` (RFC-0074) — the only `Rc`/`Arc` hits in `src/` are the
evaluator's own internal `Rc<RefCell<...>>` plumbing, unrelated to a language feature.

**A real frontmatter/reality drift, not caught by tooling.** RFC-0097's frontmatter
says `status: implemented`; `REGISTRY.md` echoes it. But `INDEX.md` says plainly that
it's "not yet implemented (issue #269) — `coherence.rs`'s `outermost_id` has no
explicit case for 'target is the impl's own generic parameter' today; it happens to
often return `None` for one by incidental name-resolution failure, not by a deliberate
check" — confirmed directly: `coherence.rs`'s `outermost_id` matches only
`TypeExpr::Named(name, _)`, falling through to a bare `_ => None` for everything else,
with no dedicated branch for a bare blanket-impl parameter. `rfc.py check`'s clean
output doesn't catch this class of drift (it checks structural consistency, not
whether a claimed mechanism is deliberate versus incidental). Worth resolving —
downgrade the frontmatter or land the real check — the same shape of finding as
Trigger 15's PR #270 (a status claim not caught by any standing mechanism, only by
direct inspection).

**The single largest spec'd-but-not-real gap remains the allocator/lifetime cluster**
— RFC-0063/65/66/67/68/73/77, nine interlocking RFCs, ratified 07-10, still 0%
implemented. This is Priority 1's own unfinished follow-through and, per the blog
cross-reference above, the thing the public narrative calls "the foundation" while
showing as if-settled syntax that doesn't exist yet.

**Consequential refusals worth naming:** RFC-0028 (Memory and Reference Model) is the
one rejection that mattered most — it cascaded into nine further refusals of the same
abandoned region-parameter direction (RFC-0025/0047/0048/0051/0056/0069/0085/0086/0087),
clearing the way for the allocator-handle + reference-type model now accepted. RFC-0046
(Linear Closure Capture) is still refused and still blocks RFC-0050's `move`-capture
mode, unresolved. RFC-0064 (fork-join `||`) was retracted outright, not deferred — only
`spawn`/`Chan<T>`/`select` survive; worth knowing since neither blog post nor
`OBJECTIVES.md` currently says this plainly anywhere else.

---

## Honest Assessment

The blog cross-reference is the good news this cycle: the project's first public
strategic statement matches its internal strategy document closely enough, on the
points that matter most (the substrate reframing, records' priority, honest hedging on
unsettled features), that it reads as genuine intent rather than after-the-fact
marketing dressed over whatever shipped. That's not a given for a project this size,
and it's worth stating as a real finding rather than assumed.

The less good news is that neither document's stated priority was where this week's
actual RFC effort went. Four new RFCs, all real and well-executed, landed in a
reference/deref ergonomics cluster that neither the blog nor `OBJECTIVES.md` ranks
above records or the allocator cluster — both of which sat untouched, one of them
(allocators) fully ratified and buildable since 07-10, ten days ago. This isn't a
failure of judgment on any single RFC — RFC-0107/0108/0109/0110 each closes a real,
verified gap — but it is exactly the pattern `OBJECTIVES.md` §1 asks each cycle to
check for, in its mirror form: not whether *some* design kept happening, but whether
the two higher-declared priorities kept not moving while a third one did.

---

## New Triggers (to be added to `OBJECTIVES.md` §3)

1. **RFC-0097 frontmatter/reality drift.** `status: implemented` in frontmatter and
   `REGISTRY.md`, but `INDEX.md` and direct inspection of `coherence.rs::outermost_id`
   agree the bare-parameter-blanket-impl orphan check is incidental, not deliberate.
   Watch whether this gets resolved (real check landed, or frontmatter downgraded) or
   quietly persists the way PR #270 did before Trigger 15 named it.
2. **Priority 1's allocator/lifetime follow-through and Priority 2's records work both
   sat still this cycle while a lower-ranked reference/deref ergonomics cluster
   (RFC-0107/108/109/110) got four new RFCs.** Watch whether the next cycle actually
   moves either higher-ranked item, or whether ergonomics-cluster churn continues to
   substitute for it — the same shape of question Trigger 9 already asks about the
   "interpreter is temporary" corollary being misapplied, applied here to priority
   ranking instead of interpreter-internals work.

---

## References

- `public/blog/introducing-metel-2026-07-15.md` — "Introducing Metel," this cycle's
  primary new source, read as strategic intent per this cycle's specific ask
- `OBJECTIVES.md` §1 (long-term objectives) and Priority 2 — the internal statements
  the blog is cross-referenced against
- `strategic-overview-2026-07-15.md` — previous cycle's snapshot
- `internal/rfcs/REGISTRY.md`, `internal/rfcs/INDEX.md` — corpus state and curated
  narrative, respectively
- `internal/rfcs/4-implemented/rfc-0097-orphan-rule-for-bare-parameter-blanket-impls.md`,
  `metel-interpreter/src/coherence.rs` — the frontmatter/reality drift finding
- `internal/rfcs/0-draft/rfc-0107-*.md` through `rfc-0110-*.md` — this cycle's actual
  RFC-writing output, the reference/deref/pattern-matching cluster
- `reports/implementation/roadmap-2026-07-07.md` — L2 status row, corroborating the
  allocator/lifetime-anchor absence-from-source finding independently
