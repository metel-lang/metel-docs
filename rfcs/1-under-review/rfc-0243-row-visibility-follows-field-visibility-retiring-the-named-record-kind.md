---
id: rfc-0243
title: "Row Visibility Follows Field Visibility: Retiring the Named Record Kind"
date: '2026-11-19'
status: under-review
updated: '2026-11-26'
tracking: 'https://github.com/metel-lang/metel-core/issues/2099'
---

> **Status — under review (2026-11-19).** Given a design-settlement tracker (2026-11-19, #2099); unmilestoned

## Summary

A struct and a `record` are the same declaration except for one bit (RFC-0120): a `record`'s declared row is visible to
structural matching, and because publishing the row publishes its fields, every field of a `record` is public. This RFC asks
whether that bit deserves a separate declaration kind, now that three things have changed since RFC-0120 and RFC-0137 argued for
it: named views name, narrow and destructure a struct's row (RFC-0109, RFC-0144, RFC-0146 to RFC-0148); the opt-in for
row-conditional impls moves from the declaration kind to an explicit, per-grant check (RFC-0202 section 6, RFC-0250
section 0 — RFC-0209's own header-entry proposal for this is superseded); and RFC-0202 needs tuple structs to satisfy
row predicates.

It lists every option discussed, with worked examples of what each gains and costs, and states a non-binding lean for what is
left after the decisions below. **The core questions are decided** (2026-11-25): bounds see the public row, the `record`
declaration kind is retired, and a nominal type must explicitly opt in to a row-based aspect *implementation* — the general
opt-in mechanism for that is deferred to RFC-0250, but the one narrow case this RFC's own migration needs (a struct regaining
a lost plain-aspect blanket match) already has a settled spelling, RFC-0250 section 0. What remains open is enums, generic
grants, opaque views, and residual matching, each tracked below against the RFC or decision that owns it; a few non-blocking
tooling questions were pruned rather than carried forward (see Open questions).

This is a design draft, now mostly settled. Proposed row bounds and binders follow RFC-0208. Other new spellings below are illustrative.

---

## Motivation

### What `record` is today

RFC-0120: `record X { … }` is identical to `struct X { … }` in every respect except that its brand is *structurally visible*, so
its declared row satisfies row bounds (RFC-0118) and is matched by row-conditional impl resolution (RFC-0121). A plain struct's row
is never visible to either (RFC-0137 section 3). Checked against the current build on 2026-11-19:

```metel
struct Handle { fd: i64, name: String }
record NamedHandle { fd: i64, name: String }
fun wants_a_record<record T: .{ .fd: i64, .. }>(t: T) -> i64 { t.fd }

wants_a_record(r)   // r: NamedHandle, accepted
wants_a_record(h)   // T0012: `Handle` is a struct, but a struct never satisfies a row bound;
                    //        declare it as a `record` instead
```

### What changed

1. **Views.** RFC-0109 names a residual (`view TicketView for Ticketing { golden_tickets }`), RFC-0144 destructures a reference into
   disjoint sub-references, and RFC-0146 to RFC-0148 bind a method's receiver to a row parameter with a bound. A struct's row is
   already named, narrowed and bound-matched inside its module. RFC-0109 section 8 says its own rule for the module boundary is
   "deliberately blunt: it forbids rather than hides", and names the missing piece: *opacity*.
2. **RFC-0209 (superseded by this RFC and RFC-0250, metel-core#1790).** Proposed row visibility as a property of a
   (type, aspect) pair, granted by a header entry (`: A` or `derives A`, RFC-0207), with a `record` gated the same way
   for marker and derivable aspects. That mechanism is what first identified `record`'s two remaining capabilities: (a)
   satisfying a row *bound* on a function parameter, and (b) matching the blanket `extend`s of *plain* aspects (granted
   by `extend` only). Neither capability is settled by RFC-0209's own mechanism anymore — (a) is this RFC's own
   Decisions block, and (b) is RFC-0250 section 0's named `using` form.
3. **RFC-0202.** A struct never satisfies a row bound, so a tuple struct (RFC-0151 section 7) cannot satisfy `Tuple` or `Dense`
   without the colon-list's checked `satisfying` entry (RFC-0202 section 6), now specified.
4. **No partial exposure.** A struct cannot expose some fields to matching, and a `record` must publish all of them. A type with a
   public `token` and a private `user` can be neither matched on `token` nor kept private on `user`.
5. **Core and the formal model.** RFC-0241 would carry one nominal-with-row kind instead of two that differ by a flag.

### The cost of keeping the kind

A third declaration kind, a parallel spec chapter (`spec.declarations.records`), a one-way "upgrade" path from struct to record,
two code paths for the same representation, and the keyword's second job as a generic parameter kind (`<record T: …>`, RFC-0186,
RFC-0208), which the declaration kind makes easy to confuse.

---

## Background: the rules in force

| Source | Rule |
|---|---|
| RFC-0120 | `record` differs from `struct` by one bit: its row is visible to bounds and row-conditional impls. All fields of a record are public and carry no modifier. Upgrading struct to record is a one-way door. |
| RFC-0137 section 3 | Every struct has a `(brand, row)`. Having a row is universal; *visibility to structural matching* is opt-in, fixed at declaration, and inherited by every residual and view. Even a full-width projection `h.{ .fd, .name }` does not satisfy a bound. |
| RFC-0109 section 8 | Residuals do not widen visibility. A private field's name may not be written in a residual type outside its module, nor in a public signature (`spec.modules.visibility.legality-3` and `legality-8`). |
| RFC-0119 | `ToRecord`/`FromRecord` are by-value, zero-cost relabellings. `to_record()` is legal only where *every* field is visible at the call site, and its result always names the full row. The struct never implicitly satisfies a row bound. |
| RFC-0221 | A name is dotted when it is a label of a row, and bare when it is a member a nominal type declares for itself. |

---

## Design space

**Decisions for this review (2026-11-25).** Structural bounds see the public fields of
the matched type, consistently inside and outside its declaring module. An exact bound
requires that public row to contain exactly the listed fields; `..` permits more. Exactness
asserts nothing about private fields and does not grant access to or construction of them. A
nominal type must explicitly opt in to a row-based aspect implementation. Anonymous
records continue to match applicable row implementations automatically. A derive request
authorizes its selected derivation to inspect the target's private fields, without exposing
those fields to ordinary structural bounds. The mechanism selecting the derivation and
the treatment of residual aspects remain open. These decisions refine the options below.
For a residual or named view, structural matching sees the intersection of the fields
present in the residual and the public fields of its brand. The named `record`
declaration kind is retired (language owner, 2026-11-25).
Migrated named records may lose plain-aspect implementations previously obtained through
row-based blanket matching; that breaking change is accepted (language owner,
2026-11-25). A future explicit grant mechanism remains open.

**Scope decision (language owner, 2026-11-25):** row-based implementations for nominal
types and their explicit selection mechanism are deferred from this settlement. The
explicit-opt-in decision remains a constraint on a future design, not a feature being
integrated now. RFC-0250 explores one possible mechanism. Existing compiler-provided
derivations remain governed by the current specification. Migration must document the
accepted loss of named records' automatically matched plain-aspect behavior.

Five questions, answered independently by the options below.

- **A. Declaration.** Is exposure a declaration *kind*, a *modifier or clause* on a struct, or *derived from field visibility*?
- **B. What does matching see?** The fields exposed by the declaration, the public fields, or the fields visible at the use site.
- **C. What does exposure grant?** (i) Row *bounds* on function parameters, where the caller passes the value explicitly. (ii) Blanket
  row-conditional `extend`s declared by a third party, which apply without the caller doing anything. (iii) Row-conditional impls the
  type's own module writes. (iv) Aspects that mean only shape (`Dense`, `Tuple`, RFC-0202).
- **D. Who consents?** The type's author (at the declaration), the impl's author (in the label names), the caller (by a conversion),
  or both parties through an explicit impl.
- **E. How do callers reach private parts of a row?** Not at all, or through a name the module chooses.

Row-conditional impls written by the type's own module (C iii) and shape-only aspects (C iv) raise no accident risk in any option
and are allowed throughout.

---

## Options

### Declaration and consent

**O1. Keep `record` as a declaration kind.** The status quo. No change to bounds or plain-aspect blanket impls.

**O2. Public row, ambient.** A struct's row, as seen by structural matching, is the row of its `pub` fields. It satisfies bounds and
matches blanket impls with no declaration. `record` is retired as a kind; "all fields public" is a struct whose fields are all `pub`.

**O3. Public row for bounds, nominal granting for impls.** Row bounds on function parameters see the public row (as O2). Foreign
blanket row-conditional impls apply to brandless rows only. A nominal type receives an aspect through an explicit,
shape-checked grant, split by whether the aspect has a body: a predicate aspect (no methods) is granted through the colon
list's checked `satisfying` entry (RFC-0202 section 6 — `struct T: satisfying A`, never `extend`); an ordinary,
by-reference-only aspect backed by an existing row-conditional impl is granted through `extend T: A using Name;`, always
named (RFC-0250 section 0). The broader case — selecting among several providers, or reusing a field-wise template that
constructs `Self` — remains open design work, explored by the rest of RFC-0250; RFC-0209's own header-entry proposal for
it is superseded, not merely deferred.

**O4. Exposure per field, through a derive.** A field is matchable only if it is exposed: `derives Exposed(.token)` names the fields,
and an optional `exposed struct` could be sugar for exposing all public fields. Exposure implies `pub`, because a bound lets generic
code read the field. It gates bounds and blanket impls alike. Two variants: **O4a** per type (`derives Exposed`, all public fields)
and **O4b** per field (with an argument list). The argument list would reinterpret RFC-0227's derivation arguments, which today name
type parameters, as labels.

**O5. Hybrid.** Bounds see the public row (O2). Exposure (O4) gates only blanket-impl matching. O3's per-(type, aspect) gate
(RFC-0202 section 6, RFC-0250 section 0) is already finer than O5's per-type gate, so O5 adds nothing for impls over O3; it
remains relevant only if per-field granularity is wanted.

**O6. `ToRecord` instead of exposure.** Two readings.
- *Reading A: convert at the call site.* To use a row-generic function with a struct, call `to_record()` first. It consumes the
  struct (RFC-0119 is by-value), is illegal outside the module if any field is private, yields a different value so mutation through
  a reference reaches a temporary, and rebuilding with `from_record` needs every field visible and bypasses constructor invariants.
  It does serve *one-off by-value* structural use (`invoice.to_record().describe()`), which needs no exposure at all.
- *Reading B: `derives ToRecord` as the exposure marker.* Possible, and RFC-0120 says tier 3 "gets tier 2's conversions for free".
  It conflates "my full row can be relabelled by code that sees every field" with "my public fields are matchable", and inherits
  ToRecord's all-or-nothing visibility, so per-field choice is lost. RFC-0209 (superseded) already declined reusing
  `ToRecord` for derivation for a reason that still holds regardless: both directions are by-value and `clone` takes
  `&self`.

**O7. Label namespacing (a complement to any of the above).** A label gains an owner, so `.ids::id` differs from `.id`. The author of
a blanket impl bounds on the namespaced label, and only fields that explicitly adopt it match. No RFC proposes this; labels today
are plain identifiers (RFC-0188, RFC-0175, RFC-0221's dotted spelling is not a namespace). It fixes accidental conformance at the
party who creates the risk, and it says *which* meaning a field has, which exposure alone cannot ("matchable" is not "as what"). It
does not protect default-namespace labels (anonymous records and ordinary functions keep ambient `.x`, `.id`), does not address
disjointness or private parts, and is a larger new concept than the exposure options.

### Rejected within question B

**Site-visible row.** Matching sees whichever fields are accessible where the program stands. Inside the declaring module a value
would match a blanket impl over `{ token, user }` and outside it would not, so one value has different methods in different modules
and coherence depends on the use site. Rejected: every option above matches against a module-independent row (public or exposed).

### Private parts of a row

**V1. Status quo.** A public signature may not name a private field (RFC-0109 `legality-8`); a method that touches private state
takes the whole `&var self`.

**V2. Opaque views.** A `pub` view declared in the struct's module whose field list is not visible outside it, usable in public
signatures and borrowable by callers (RFC-0109 section 8's "missing piece", Niko Matsakis's abstract fields). To keep disjointness
from public fields free, an opaque view covers *private fields only*, so it is disjoint from every `pub` field by construction.
Callers can hold, pass and split the borrow; they cannot read, write or destructure it. Four policies for disjointness *between*
opaque views:
- **D1.** Overlapping unless declared `disjoint`.
- **D2.** Disjointness derived from the module's own check and exported automatically.
- **D3.** Parts declared on the struct (partitions), so disjointness is the definition.
- **D4.** Treated as ordinary API, listed by tooling, no new syntax.

### Add-ons

- **Lint.** Flag a blanket impl bounded on a bare primitive field type (`id: i64`); a semantic type (RFC-0200 newtype) is far harder
  to match by accident.
- **Aspect in scope.** Require the aspect to be in scope for method-call syntax, if Metel does not already (not checked). It narrows
  where an accidental method is visible and does not remove it.

### Comparison

| | Existing structs unchanged | Bounds on a struct | Third-party blanket impls on a struct | Partial exposure | New concept | RFC disruption |
|---|---|---|---|---|---|---|
| O1 | yes | records only | records only (plain aspects) | no | none | none |
| O2 | no, they start matching | all `pub` fields | all, ambient | via `pub` | none | RFC-0120 retired; RFC-0137 section 3 amended |
| O3 | no for bounds | all `pub` fields | by explicit entry per aspect | via `pub` | colon-list `satisfying` (RFC-0202); `extend ... using Name` (RFC-0250) | RFC-0121 narrowed; builds on RFC-0202 and RFC-0250 |
| O4a | yes | exposed types | exposed types | no | `Exposed` | small |
| O4b | yes | exposed fields | exposed fields | yes | `Exposed` + labels as derive args | small, plus RFC-0227 |
| O5 | no for bounds | all `pub` fields | exposed (per type or field) | yes | `Exposed` | small |
| O6 A | yes | by conversion | by conversion | no | none | none |
| O7 | depends | with adoption | with adoption | via adoption | namespaced labels | RFC-0175, RFC-0188 |

---

## Worked examples

Marked *verified* when run against the build on 2026-11-19. The rest are illustrations: the spellings are invented, row-conditional
impl resolution is still gated on RFC-0121, and the borrow examples cannot run because RFC-0122 is not enforced.

**E0. Baseline (verified).** The `Handle` / `NamedHandle` program in the Motivation: the record is accepted, the struct fails with
`T0012` and a message that tells the author to change the declaration kind.

**E1. Partial exposure (O2, O4b).**

```metel
struct Session { pub token: Token, user: String }       // O2: only `token` is public, so only `token` matches
fun refresh<T: .{ .token: Token }>(t: &var T) { … }
refresh(&var session);                                  // OK from any module
```

In this proposed bound, `T` retains the Session brand. Extracting `..T` for public structural matching yields only `token`; a row binder matching the remaining fields receives an empty row.

Today `Session` is a struct (never matches) or a record (`user` forced public). Under O4b the same would be
`struct Session { pub token: Token, pub id: i64, user: String } derives Exposed(.token)`, and a bound on `.id` would be rejected with
"field `id` is public but not exposed".

**E2. Callers borrow private state through a public name (V2).**

```metel
struct Experiments { names: List<String>, data: List<f64>, pub label: String }
pub opaque view Entries for Experiments { names, data }          // invented spelling
extend Experiments { pub fun add(&var self: Entries, n: String, d: f64) { … } }

// another module
let entries := &var e.Entries;     // private part, by its public name
let label   := &e.label;           // `pub`, disjoint from Entries by construction
e.add("run-1", 0.5);
```

Under V1, `add` must take the whole `&var self`, which also borrows `label`.

**E3. A better diagnostic (O2, O3).** T0012 stops saying "declare it as a record" and says that a field is private or not exposed, a
local fix at the field.

**E4. Accidental conformance (O2).**

```metel
// library
pub aspect Identified { fun describe(&self) -> String; }
extend<..R> .{ .id: i64, R }: Identified { … }

// downstream
struct Invoice { pub id: i64, pub total: f64 }    // id = invoice number
struct Order   { pub id: i64 }                    // id = database key
invoice.describe();    // compiles under O2: the blanket impl applies to both, unasked
```

Under O1 neither type matches. This is the ambient-matching worry of RFC-0116 section 5 and RFC-0090 section 8, and the strongest
argument for keeping an opt-in.

**E5. Adding a public field (O2).** A library adds `pub port: i64` to `Config { pub host: String }`. If two other libraries'
blanket impls over `{ host }` and `{ port }` provide the same method name for *different* aspects, `cfg.describe()` becomes
ambiguous in downstream code that did not change. For the *same* aspect the overlap should be rejected at the impls' definition,
whatever structs exist: the implemented row-conditional coherence rule rejects conditions that are not provably disjoint
(RFC-0121 and `spec.types.generics.row-conditional-impls.legality-3`). The remaining hazard is a
call-site ambiguity across aspects, resolved by a qualified call. Adding a *private* field is invisible outside the module.

**E6. Why matching uses the public row (rejected site-visible row).** With `struct Session { pub token: Token, user: String }` and
blanket impls A over `{ token }` and B over `{ token, user }`, a site-visible rule gives `s.describe()` = B inside the module and A
outside.

**E7. Disjointness is a promise (V2).** `Entries` over `{ names }` and `Audit` over `{ data }` let a caller hold `&var e.Entries`
and `&var e.Audit` together. If the module later makes `Audit` also need `names`, those callers stop compiling. D1 makes the promise
an explicit `disjoint` declaration.

**E8. `to_record` as the mechanism (O6 A).**

```metel
let r := session.to_record();        // consumes `session`; illegal outside the module (private `user`)
refresh(&var r);                     // mutates the record, not the original
session := Session::from_record(r);  // needs every field visible; bypasses constructor invariants
```

**E9. Explicit nominal granting (O3), now specified: RFC-0250 section 0, for an aspect with a body.**

```metel
// two live declaration spellings, neither ruled out (RFC-0250 section 6):
pub named extend IdentifiedById<..R> .{ .id: i64, R }: Identified { fun describe(&self) -> String { … } }
// or:
pub extend IdentifiedById<..R> .{ .id: i64, R } for Identified { fun describe(&self) -> String { … } }

struct Invoice { pub id: i64, pub total: f64 }
invoice.describe();                          // error: Invoice does not implement Identified
extend Invoice: Identified using IdentifiedById;  // checked against the shape: the public row has `.id: i64`
invoice.describe();                          // OK
```

`Order` never opts in and never gets `describe`. The provider is always named, even though `IdentifiedById` is the only
legal match for `Identified` here (RFC-0121's coherence forbids a second, overlapping one) — naming is for the reader,
not to disambiguate. This is also the migration bridge: a `record Invoice` retired into a `struct` that automatically
matched `Identified`'s blanket impl regains it with this one line, per lost (type, aspect) pair. A *pure marker* aspect
(no methods, like `Positive`) uses the colon list instead (RFC-0202 section 6: `struct Config: satisfying Positive;`),
never this form.

**E10. Migration (O2, O3).**

```metel
record Handle { fd: i64, name: String }   →   struct Handle { pub fd: i64, pub name: String }
```

Mechanical. Only the declaration kind goes away; `record` as a parameter kind (`<record T: …>`, RFC-0186) stays. Under O4 the exact
equivalent is `struct Handle { pub fd: i64, pub name: String } derives Exposed`, which changes no existing struct.

---

## Non-binding lean

Stated so the discussion has a target. Points 1 and 3 are now decided (2026-11-25, Design space above); the rest remain a
non-binding lean.

1. **Bounds see the public row** (the bound half of O2). **Decided.** The caller passes the value explicitly, a bound only
   reads fields already public, and adding a public field can only widen what satisfies a bound, so gating bounds buys little.
2. **Impl granting is per (type, aspect).** A predicate aspect (no methods) is granted through the colon list's checked
   `satisfying` entry, specified: RFC-0202 section 6. A by-reference-only aspect backed by an existing row-conditional
   impl is granted through `extend T: A using Name;`, always named: the narrow case is specified, RFC-0250 section 0. The
   general case, several candidate providers, label mapping, or an aspect's own declared template, is deferred to the
   rest of RFC-0250. This makes a per-type `Exposed` marker unnecessary for impls, and it is finer than O5.
3. **Retire the `record` declaration kind.** **Decided.** A record is now a struct with public fields plus whatever grant
   mechanism applies — RFC-0202 section 6 for a predicate aspect, RFC-0250 section 0 for a behavior-bearing one, the rest
   of RFC-0250 for the general case. The `record` parameter kind stays.
4. **Opaque views (V2) with D1**, staged after reference rules and borrow checking, because they need disjointness reasoning.
5. **`ToRecord` unchanged** (O6): convert when you want a different value, grant when you want the same one accepted.
6. **Label namespacing later** (O7), in the label RFCs. It composes with the above: adoption only narrows what a field matches.
7. **The primitive-label lint** as a convention enforced by tooling, not a language rule — tracked as tooling work, not an
   open design question.

If the per-field granularity of O4b is wanted regardless, it can be added later as a finer gate without changing the rest.

---

## Migration

Under O2 or O3, every `record X { a, b }` becomes `struct X { pub a, pub b }` (mechanical), and the spec's struct-to-record upgrade
section is deleted. Under O4 a record becomes `struct … derives Exposed`. `Copy` is already `declared` (RFC-0212), so any type —
record or struct — already needs a header entry (`derives Clone`/`copy struct`) for it today, independent of this RFC; a migrated
record needing the same entry is nothing new. Existing structs start satisfying bounds under O2 and O3; under O1
and O4 they do not.

## Interactions

- **RFC-0120** (implemented): superseded in part by O2, O3 or O4 (the kind goes; the capability moves).
- **RFC-0137** (integrated): section 3's eligibility becomes a property of the public (or exposed) row instead of a brand flag. Its
  worked example (`h.{ .fd, .name }` rejected "because if it satisfied the bound, declaring `record` would buy nothing") describes the
  outcome O2 accepts. Residuals: whether a narrowed residual's public row is the intersection with the narrowing is open.
- **RFC-0109** section 8: V2 is its open "opacity" question. Self-view narrowing never crosses the module boundary, so it is unaffected.
- **RFC-0209** (superseded by this RFC and RFC-0250): originally the per-aspect gate O3 was framed on; O3's actual
  mechanism no longer needs it. Its open question 4 (a template reading fields the module keeps private) lapsed with it
  and is unowned — it would resurface if RFC-0250's general case ever needs private-field authority.
- **RFC-0119** (accepted): unchanged under every option except O6 B.
- **RFC-0121, RFC-0060**: row-conditional impls and their coherence; O3 narrows the first, and the same-aspect overlap check in E5
  depends on the second.
- **RFC-0202**: tuple structs with public numeric fields satisfy `Tuple` and `Dense` directly under O2 and O3, via section
  6's colon-list `satisfying` entry — the predicate-aspect half of O3's spelling.
- **RFC-0250**: section 0's `extend T: A using Name;` is O3's spelling for a by-reference-only plain aspect backed by an
  existing row-conditional impl, always named; this RFC's migration gap is its motivating example.
- **RFC-0207, RFC-0212, RFC-0227**: `derives` and its arguments, the vehicle for O4; RFC-0212's `declared` property is
  what RFC-0202's `satisfying` refines for the predicate-aspect case above.
- **RFC-0221, RFC-0188, RFC-0175**: the dotted-label rule (bare members versus row labels) supports "a struct's fields are not labels
  until projected through the exposed row"; O7 lives here.
- **RFC-0186, RFC-0192, RFC-0208**: the `record` and `..R` parameter kinds, unchanged.
- **RFC-0116, RFC-0225**: anonymous records keep matching every template.
- **RFC-0151**: tuples as rows; tuple structs.
- **RFC-0241** section 7.3 and 7.9: one nominal-with-row kind in Core; opaque views as abstract places are the worked example for
  Stage 2 (structural disjointness). **RFC-0242** (library-defined references and place access) overlaps V2 and should be read with it.
- **RFC-0200** (newtypes): the semantic-field-type convention in the lint.

## Alternatives considered

1. **Make every struct row-visible, impls included.** Declined by RFC-0137 and RFC-0209 (superseded); E4 is the
   reason, and it stands on its own regardless of RFC-0209's fate.
2. **A brand parameter kind** (`extend<struct S, ..R> …`). Declined by RFC-0209 (superseded): the gate returns under
   another name — still true of O3's actual mechanism.
3. **Matching against the site-visible row.** Rejected (E6).
4. **Abolish views or keep the blunt rule.** V1 keeps the gap between "public name" and "private parts" that RFC-0109 section 8 names.
5. **Make every struct a record** (the thesis "every struct is `(brand, row)` and visible"). RFC-0120 deliberately does not claim it;
   it is the endpoint of O2 with impls included.

## Risks

- **Accidental conformance** is the real semantic cost of dropping the opt-in for impls (E4). O3, O4, O5 and O7 each address it.
- **Public fields become a matching contract** under O2 and O3: adding one is visible to bounds. It is bounded and explicit (E5).
- **Two visibility axes** (access versus matching) under O4, and a per-(type, aspect) axis under O3's actual mechanism
  (RFC-0202 section 6, RFC-0250 section 0).
- **Opaque views need a place algebra** the borrow checker does not have yet.
- **Churn on integrated and implemented RFCs** (RFC-0120, RFC-0137, RFC-0121).

## Open questions

1. **Resolved (2026-11-25).** Bounds see the public row (the bound half of O2); the `record` kind is retired; a nominal type
   opts in to a row-based impl explicitly. The narrow opt-in cases are RFC-0202 section 6 (a predicate aspect) and RFC-0250
   section 0 (a by-reference-only aspect backed by an existing impl, always named); the general case is deferred to the
   rest of RFC-0250.
2. Bounds: public row, as decided above. *(Resolved — see 1.)*
3. **Resolved for the narrow case:** a plain aspect's opt-in is `extend T: A using Name;` (RFC-0250 section 0), always
   named. RFC-0209's header-entry mechanism, which this question originally asked about extending to plain aspects, is
   superseded — the question of a header-entry-style grant lapses with it rather than carrying forward as unresolved.
4. A selected derivation may inspect private fields as decided above. How that authority is represented and constrained
   remains open — tracked with RFC-0250, since it only arises for the general (not the narrow, by-reference-only) case.
5. A narrowed residual's public row is its present fields intersected with the brand's
   public fields. RFC-0137 section 3's worked example needs amendment at integration.
6. **Enums:** variant rows and first-class variant types are under review in RFC-0210. A
   struct-style row bound does not match an enum merely because one variant has the
   required fields. This settlement does not define a variant-wise matching mechanism.
7. **Generic nominal grants:** a grant may be conditional on generic arguments. Its
   declared condition is part of the applicable aspect interface and must be sufficient
   for the selected implementation's requirements (language owner, 2026-11-25). Exact
   grant syntax, provider selection and overlap checking are explored in RFC-0250;
   derived field-wise flows remain governed by their own rules.
8. Opaque views are deferred to RFC-0251, including disjointness and composition.
9. **Row coherence:** the current spec rejects same-aspect row-conditional impls unless
   their conditions are provably disjoint; the frontend implements overlap checking and
   has a `T0015` fixture for `{ a, .. }` versus `{ b, .. }`. Current brand-specific impls
   take priority over matching row-conditional impls; RFC-0250 section 0's grant
   materializes an ordinary impl, so this priority already covers it with no new rule. How
   explicit *provider* selection interacts with that priority for the general, multi-provider
   case remains an RFC-0250 question, non-blocking for this RFC's own narrower scope.

Three non-blocking items were pruned from this list rather than carried forward (PROCESS.md's "prune harder" rule): the
primitive-label lint and aspect-in-scope rule are tooling conventions, not open design questions (lean point 7); label
namespacing already has an owner, "later, in the label RFCs" (lean point 6); and the `#derive(ToRecord, FromRecord)`
spelling in RFC-0119 predating the `derives` clause is confirmed true but is RFC-0119's own open question 1 to resolve, not
a question this RFC needs to carry.

## Implementation notes

Not started. A plausible order: the colon-list `satisfying` entry (RFC-0202 section 6) and the public-row bounds rule
together, since neither waits on the other; then RFC-0250 section 0's named `using` form for behavior-bearing aspects; then
retire the `record` declaration kind and amend RFC-0137 section 3 and the spec chapter; then opaque views after
reference rules and borrow checking (RFC-0122), as a user of RFC-0241's place algebra; then label namespacing if wanted.
RFC-0209's superseded header-entry mechanism contributes nothing further to this order.

---

## Decision

**Outcome:** *(pending)*
