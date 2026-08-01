---
id: rfc-0091
title: "Linear Records"
date: '2026-07-09'
status: draft
target:
updated: '2026-07-24'
---

> **New RFC, split out 2026-07-09** from `reports/substructural-types/linear-types.md`
> §3 (Option C) and `structural-records.md`'s per-field-multiplicity content, as part of
> decomposing an oversized RFC-0012 into smaller, independently reviewable pieces. This
> is explicitly the "fuller vision" layered on top of two already-sufficient RFCs:
> RFC-0089 (Linear Types) plus RFC-0090's `{ … }` former/tier 2 already satisfy RFC-0063 §9
> item 5's deadline via explicit `.to_record()`/`.from_record()` conversion, with no
> dependency on this RFC. Everything here is additive, paced exploration, not gating
> work — consistent with `strategic-overview-2026-07-08.md`'s classification of this
> whole thread as "paper-only territory," not yet validated against a real
> implementation.
>
> **Revised 2026-07-09, later the same day**, matching RFC-0089's own revision: the
> "floor" this RFC builds on top of is no longer "RFC-0089's Option B (raw field access
> off a nominal struct)" — that mechanism was dropped. RFC-0089 §3 now specifies the
> floor as conversion through `ToRecord`/`FromRecord` (RFC-0090) instead. This RFC's own
> content is unaffected in substance: Option C (automatic downgrade, no explicit
> `.to_record()` call needed at the point of consumption) is still the more expressive,
> additive extension on top of that floor — the contrast is now "explicit conversion
> call, then move" vs. "no conversion call needed, the compiler downgrades the type
> automatically," rather than "raw struct field access" vs. "records."
>
> **Revised 2026-07-24 — mechanical syntax sweep, no semantic change.** RFC-0090 dropped
> the `record` keyword from the anonymous type-former, so every `record { … }` here is now
> `{ … }`, and anonymous record *values* separate with `=` (`{ host = "example.com" }`) per
> the `:` classifies / `=` defines invariant. Nothing about this RFC's own content changes.
>
> **One visible inconsistency this leaves, deliberately, because it is accurate:** §2.3's
> examples read `RequestBuilder { data: { host = "example.com" } }` — the *struct literal*
> still separates with `:`, the *record value* inside it with `=`. That mismatch is real
> and current: RFC-0090's record values are settled, while RFC-0115 (which would make the
> struct literal `data = …` too) is only `0-draft`. Left as-is rather than pre-applying an
> unaccepted RFC; if RFC-0115 lands, one more mechanical pass makes these uniform.
>
> **`HasField`/`Lacks` swept later the same day — see the final note below.**
>
> **Also revised 2026-07-24 — §5's `drain_field` row-extension notation normalized to
> `..R`.** Its signature read `(s: &mut { name: T | R }) -> (T, &mut { R })`, using two
> notations for row extension in one function and neither of them the corpus's normative
> one. `| R` appeared **nowhere else in the corpus** except the copy of this same signature
> in `reports/substructural-types/structural-records.md`, which this RFC was extracted from
> — it is a leftover from that split, not a competing convention. The normative spelling is
> RFC-0090 §2's spread tail, `{ x: f64, ..R }`, used consistently in RFC-0090, this RFC's
> own §2.3, `brand-types.md`, and `access-and-presence-rows.md`. The return type's bare
> `{ R }` (row variable with no marker at all) is normalized the same way. No semantic
> change — `{ name: T, ..R }` and `{ name: T | R }` denote the same row.
>
> *(Where `{IO | E}` appears elsewhere in the corpus it is quoting **Koka's** effect-row
> syntax as prior art, not proposing Metel syntax; `access-and-presence-rows.md` §4 writes
> the two side by side as equivalents, `{IO | E}` / `{ IO, ..E }`.)*
>
> **Revised once more 2026-07-24 — `..R` at generic-argument positions too.** RFC-0090
> adopted the rule that **`row` declares and `..` marks every use**, so a row variable is
> `..R` wherever it appears in a type and a bare identifier in type position is always a
> *type* variable. §2.3's `RequestBuilder<R>` becomes `RequestBuilder<..R>`; the binder
> `<row R>` is unchanged. The forcing case was elsewhere — `Handle.{ R }` versus
> `Handle.{ fd }` inside projection braces was genuinely ambiguous between a row variable
> and a field label — but the rule is uniform, so this RFC follows it.
>
> **Final revision 2026-07-24 — `HasField`/`Lacks` swept.** RFC-0090 retired both on
> 2026-07-23 in favour of bare rows; this RFC was the last cluster member still using
> them. §1's prose (`the residual is still HasField<"fd", i64>`), §2.3's two impl bounds,
> and two call-site comments are converted:
>
> | was | now |
> |---|---|
> | `HasField<"fd", i64>` | `{ fd: i64, .. }` |
> | `impl<row R: HasField<"auth", String>>` | `impl<row R: { auth: String, .. }>` |
> | `impl<row R: Lacks<"auth">>` | `impl<row R: !{ auth: _ }>` |
>
> **The trailing `..` on the positive bounds is not cosmetic.** A `HasField` bound was
> always existential — "has at least this field" — so under the `..` rule adopted earlier
> today it needs the marker to keep that meaning. Dropped, each would now read as "this
> row is *exactly* `{ auth: String }`", which would break every one of these examples: the
> builder's whole point is that `R` carries `host` and whatever else besides. The negative
> bound takes no `..`, since absence has no rest to quantify over.
>
> **`RequestBuilder<R + "auth">` fixed later the same day, via RFC-0090 §2.1's resolution
> of open question 14.** Row extension turns out to need no operator: it is
> `RequestBuilder<{ ..R, auth: String }>`, this cluster's own spread tail, with the label
> written where labels are normally written. The string literal was only ever there
> because an infix operator had nowhere else to put the name. Removal — the other half of
> that question — becomes a where-clause decomposition, which this RFC does not currently
> use anywhere.
>
> **Note the `_` in `!{ auth: _ }` is itself not yet buildable** — a type-position
> wildcard does not exist (`_` appears only in `pattern`), tracked as RFC-0090 open
> question 12. This sweep adopts the spelling RFC-0090 settled on; it does not make it
> parse.

> **Status — under review (2026-07-21).** Reviewing the records/views substrate cluster together, per OBJECTIVES.md Priority 1 (reordered 2026-07-22). The cluster's first deliverable is the record/row semantics themselves -- RFC-0090 SS3 step 1's closed `{ … }` type-former plus bare-row bounds -- not the `ToRecord`/`FromRecord` conversions the blog names, which are tier 2 of RFC-0090 SS8 and convert into a type-former that must exist first. Thorough draft with a substantiated primary proposal; open questions remain, chiefly the RFC-0089/RFC-0090 dependency direction that Trigger 6 tracks.

> **Status — draft (2026-07-24).** Deferred 2026-07-24: per-field multiplicity waits until records are implemented. The RFC-0090 coupling was introduced by accident (RFC-0089's 2026-07-09 same-day revision rewrote its floor from Option B to ToRecord), which is why Trigger 6 could observe that neither RFC states the conflict. Returned to draft so the records cluster is not gated on it and the review backlog reflects what is actually reviewable.

## Summary

Extends the RFC-0089/RFC-0090 partial-consumption floor (explicit `.to_record()`/
`.from_record()` conversion, then move) with Option C: automatic downgrade, where a
mixed-multiplicity struct's binding type changes at the point of partial consumption to
reflect exactly which fields remain, with no explicit conversion call needed, using
RFC-0090's row/record machinery. Resolves the long-standing aliasing question that
blocked Option C — what type does a borrow taken before the downgrade have afterward —
with a candidate (not proven) answer: the shrunk row type, sound because `&mut` already
guarantees no other alias exists to observe the stale type. Also specifies a
`Drop`-field-usage declaration (`uses (fd)`) that narrows RFC-0071 §7's blanket ban on
partial moves out of `Drop` types to only the fields a `Drop` impl actually reads.

---

## Motivation

RFC-0089/RFC-0090's floor (explicit `.to_record()`, move, `.from_record()`) is
sufficient and unblocks Phase 3, but it requires every consuming function to manually
convert and re-convert, and to manually thread the non-linear remainder through its own
return type — workable, but it means the *type itself* never reflects "which fields
have already been consumed" for a value held across multiple calls without an explicit
conversion at each step. Option C makes that reflection automatic: the compiler tracks
it as part of the type, the same way RFC-0090's row-conditional typestate tracks
protocol state. It also closes a gap
RFC-0071 §7 leaves open: partial moves out of `Drop`-implementing types are banned
outright, wholesale, even when the fields being moved out have nothing to do with what
`Drop::drop` actually reads.

---

## 1. Declared field-usage narrows RFC-0071 §7's blanket `Drop` ban

RFC-0071 §7 bans *any* partial move out of a type that implements `Drop`, regardless of
which fields `drop` actually touches. Recursive per-field drop already safely handles
fields piecemeal — the real danger is narrower: a *custom* `Drop::drop` body is
arbitrary code that might read *any* field, and the compiler has no way to know which.
Proposed resolution: let a `Drop` impl **declare** which fields its body depends on:

```metel
extend Handle: Drop {
    fun drop(self: Handle) uses (fd) {
        close_fd(self.fd);
    }
}
```

— checked (not just asserted) against the method body, so `tag` may be moved out of
`Handle` first (the residual is still `{ fd: i64, .. }`, all `drop` needs) while
moving `fd` itself out remains rejected. Declared rather than inferred, for the same
reason this whole cluster has repeatedly preferred explicit-and-checked over
implicit-and-inferred (RFC-0065's elision-is-never-a-silent-choice principle, Storage
Transparency): inferring field usage from the body means an unrelated internal change
to `drop` silently changes which partial-move patterns are legal everywhere else, an
action-at-a-distance failure mode.

**Not resolved:** if `drop`'s body calls a helper method, "what does this actually
touch" has to become transitive across that call — either the helper needs its own
declared field-usage that composes through, or field-usage becomes a real effect
system (possibly an application of `algebraic-effects.md`'s already-planned effect
system rather than a fourth new mechanism).

**Novelty check:** no mainstream language does this as far as this exploration is
aware — Rust's restriction is exactly as blunt as Metel's current one, for the same
reason (no per-`Drop`-impl field-dependency tracking exists there either).

### 1.1 A real motivating case: `Rc`/`Arc`'s own internal teardown

`Rc`/`Arc`'s own internal allocation struct has exactly this shape, and mainstream
implementations resort to `unsafe` specifically because their type systems can't
express it safely:

```metel
struct RcBox<T> {
    strong: AtomicUsize,
    weak: AtomicUsize,
    value: T,
}

extend<T> RcBox<T>: Drop {
    fun drop(self: RcBox<T>) uses (value) {
        drop(self.value);
    }
}
```

When the last *strong* handle drops, `value` must be torn down immediately, but the
allocation can't be freed yet if any *weak* handle still exists. `value`'s lifetime is
provably shorter than `strong`/`weak`'s, and teardown genuinely happens in two phases:
drop `value` now, keep the counters valid and readable until weak also reaches zero,
only then deallocate. Rust's real `Rc`/`Arc` cannot express "drop half this struct,
leave the rest alive" safely in the type system, so it does this with raw pointers and
`ManuallyDrop` instead.

**This is a narrow point of contact with `Rc`/`Arc`, not a claim that this mechanism
implements them.** It only covers the teardown-ordering detail. The reference-counting
and aliasing semantics that make `Rc`/`Arc` what they are — many handles sharing one
allocation, an atomic count mutated through shared references, a dynamic uniqueness
check for `get_mut` — are a different axis entirely (shared, dynamic,
many-handles-one-resource, checked at runtime) from what per-field multiplicity
provides (exclusive, static, one-owner-many-fields, checked at compile time). That axis
already has a purpose-built answer in this cluster: `brand-types.md`'s `RcToken`. The
two mechanisms divide the labor cleanly: `RcToken` for who may share and mutate; this
RFC's `uses (...)` declaration for how the shared allocation's own internal struct
tears itself down.

---

## 2. Option C: automatic downgrade via records

Once RFC-0090's `{ … }` type-former exists, a partial-consumption residual stops being
a bespoke, invisible marker — it *is* a record type. Consuming `Foo { a: A, b: B }`'s
field `a` produces a value typed `{ b: B }`: the struct's own remaining fields,
literally. Since a record containing a linear or `Drop`-needing field is itself
linear/drop-relevant by the same structural composition rule as ordinary structs, "the
remainder still needs consuming" is no longer a rule anyone had to write — it's the
same fact, restated.

RFC-0090's tier 2 (`ToRecord`/`FromRecord`, including the borrowed `to_record_mut`/
`from_record_mut` variants) already supplies the exact mechanism this needs — Option C
is not a separate row-tracking system, it is tier 2 applied to a type with
mixed-multiplicity fields.

### 2.1 The aliasing question, and a candidate answer

The long-standing blocker on Option C: if `p = &f` was taken before the downgrade, what
type does `p` have afterward? **Candidate answer:** `p`'s type becomes the shrunk row
(`&mut { <remaining fields> }`), sound for an unremarkable reason — `&mut`
already guarantees no other live reference exists to observe the stale, pre-downgrade
type, so no new aliasing machinery (a brand, a fork/join token) is needed beyond
ordinary `&mut` exclusivity and structural row equality.

This is **promising, not proven**: no formal soundness argument has been written down,
only a worked mechanism plus several worked examples (§3 below) that exercise it
without incident. Option C should still be treated as unratified until this gets a real
argument, not just examples that haven't broken it.

### 2.2 Reusing `(row, brand)` for nominal residuals

RFC-0090 §9 notes that if a struct is already internally `(row, brand)`, the residual
after consuming one field is just `(row - field, brand)` — the *same* thing negative row bounds (`!{ field: _ }`, RFC-0090 §4)
already names for open records, applied to a nominal residual with its brand held fixed
rather than erased. That would make nominal partial consumption and RFC-0090's
row-conditional typestate one mechanism applied to two syntactic forms, rather than two
designs that need separately justifying and separately maintaining. A row gives the
downgrade a precise strong-update semantics (shrink the row, keep the brand) and — because
a row decomposes a value into named slots the checker can already reason about
independently — lets borrow exclusivity be checked per *field* rather than only per
whole struct, narrowing exactly what must be un-borrowed for the consumption to be
legal. Promising, not proven; no soundness argument is written down here either, only
the shape of one.

**A second application of the same idea, added 2026-07-10:** RFC-0089 §3.1 reuses
`(row, brand)` for a different purpose than this section's residual identity —
preserving a *fiat*-linear struct's nominal origin through an ordinary tier-2
`ToRecord` conversion, so a derive-emitted `impl Linear` can target that specific
branded shape instead of the conversion's `Linear` status silently reverting to
whatever the bare row implies. Worth noting here because it's the same underlying
move (a brand riding along with a row after a struct-to-record conversion) applied to
a second problem, not a third mechanism.

---

## 3. Worked examples

Three examples, each showing a different facet of what tracking multiplicity per field
(rather than once for the whole struct) actually buys.

### Why whole-value `Drop` isn't enough, concretely

```metel
struct Connection { socket: Socket, stats: ConnStats }

extend Connection: Drop {
    fun drop(self: Connection) {
        self.socket.close_if_open();
    }
}

fun close_and_report(c: Connection) -> ConnStats {
    let stats = c.stats;   // ERROR today: partial move out of a Drop type is banned
                           // outright, even though `stats` has nothing to do with
                           // what `drop` actually touches
    c.socket.close();
    stats
}
```

`stats` never needed any consumption discipline at all — it only inherited one because
it happened to share a struct with `socket`. With §1's declared field-usage on `drop`,
the residual left after moving `stats` out stays exactly as droppable as it needs to be:

```metel
extend Connection: Drop {
    fun drop(self: Connection) uses (socket) {   // declares: drop only ever touches `socket`
        self.socket.close_if_open();
    }
}

fun close_and_report(c: Connection) -> ConnStats {
    let stats = c.stats;      // fine now — residual { socket: Socket } is still
                              // Drop-eligible on its own, and dropping it only reads
                              // `socket`, which is still there
    c.socket.close();
    stats
}
```

### Tier 2's `to_record_mut`/`from_record_mut`: static absence, not a runtime check

```metel
@derive(Linear, ToRecord, FromRecord)
struct FileHandle {
    fd: RawFd,     // the reason FileHandle as a whole is Linear
    path: String,  // ordinary data, no consumption discipline
}
```

(`Linear` here is RFC-0089's auto-impl aspect, granted structurally because `fd` is
multiplicity-`1` — no `@derive(Linear)` annotation is actually needed or meaningful;
shown for illustration only. `ToRecord`/`FromRecord` are the derivable ones.)

```metel
fun take_fd(h: &mut FileHandle) -> (RawFd, &mut { path: String }) {
    let view = h.to_record_mut();
    let fd = move view.fd;
    (fd, view)          // view's residual type, { path: String }, is not Linear —
                         // RFC-0090 §5's field-composition rule applies to records
                         // exactly as it does to structs, and `path` alone carries no
                         // obligation
}

fun log_path(view: &{ path: String }) {
    println("still open at: ${view.path}");
    // view.fd doesn't typecheck here at all. Compare to fd being declared Perhaps<RawFd>
    // instead: every read site would need a match/unwrap to find out it's gone. Here
    // the caller's own parameter type already says so — checked once, at compile time.
}

fun release(view: &mut { path: String }, fd: RawFd) -> &mut FileHandle {
    view.fd = fd;
    FileHandle::from_record_mut(view)
}
```

### Tier 3's row-conditional impls, the construction direction

Per-field multiplicity is equally about a field going from absent (0) to present (1)
exactly once — RFC-0090 §4's "builders, in the dual direction" claim:

```metel
struct RequestBuilder<row R> { data: { host: String, ..R } }

extend<row R: !{ auth: _ }> RequestBuilder<..R> {
    fun with_auth(self, token: String) -> RequestBuilder<{ ..R, auth: String }> {
        RequestBuilder { data: { ..self.data, auth = token } }
    }
}

extend<row R: { auth: String, .. }> RequestBuilder<..R> {
    fun send(self) -> Response { ... }
}

fun main() {
    let req = RequestBuilder { data = { host = "example.com" } }
        .with_auth("secret");
    req.send();
    // req.with_auth("again");                        -- R no longer satisfies !{ auth: _ }
    // RequestBuilder { data: { host = "x" } }.send()  -- needs { auth: _, .. }
}
```

### More unsafe-in-Rust gaps this model would close

Three further real, documented Rust patterns where `unsafe` exists specifically because
the type system can't reason about part of a struct changing while the rest stays
valid. **Scope, stated plainly:** this is not a claim that `unsafe` becomes unnecessary
generally — FFI, raw pointer arithmetic, and address-stability concerns (`Pin`,
self-referential structs) are a different problem this model says nothing about. It is
specifically the partial-struct-manipulation slice of `unsafe` these examples target.

**Swapping a field's value with no cheap placeholder available.** `mem::replace` needs
*some* value of the field's type to put in the slot temporarily; when no cheap or
semantically valid one exists, real code falls back to `unsafe { ptr::read }`/
`ptr::write` — packaged, for exactly this reason, by crates whose entire purpose is
wrapping this one unsafe operation, which must additionally abort the process on panic,
because there is no safe way to represent "this slot currently holds no valid value of
any kind" if the transformation closure unwinds partway through:

```rust
struct Session { host: String, state: AuthState }
enum AuthState { Connected { socket: Socket }, Authenticated { socket: Socket, token: String } }

fn authenticate(session: &mut Session, token: String) {
    let old = std::mem::replace(&mut session.state, /* ??? */);
    session.state = match old {
        AuthState::Connected { socket } => AuthState::Authenticated { socket, token },
        other => other,
    };
}
```

```metel
@derive(ToRecord, FromRecord)
struct Session { host: String, state: AuthState }

fun authenticate(session: &mut Session, token: String) {
    let view = session.to_record_mut();   // &mut { host: String, state: AuthState }
    let old_state = move view.state;       // view narrows to &mut { host: String } —
                                            // `state` is genuinely absent here, not holding
                                            // a placeholder value of any kind
    let new_state = match old_state {
        AuthState::Connected { socket } => AuthState::Authenticated { socket, token },
        other => other,
    };
    view.state = new_state;                // view widens back to the full row
    Session::from_record_mut(view);
}
```

No placeholder is ever needed, because the row can represent "no value here at all" as
a first-class static fact. A likely additional benefit, not fully worked out here: if
the transformation panics between the two lines, the residual `view` (`{ host:
String }`) is an ordinary, fully-valid value — dropping it should fall out of the same
field-composition Drop rule this RFC already relies on.

**Piecewise struct construction, field by field.** Real code needing to build a struct
incrementally uses `MaybeUninit` plus per-field `unsafe` writes plus a final
`assume_init()`, and has to handle a genuine hazard along the way: if a later field's
computation panics, the fields already written need manual unsafe drop handling or they
leak:

```rust
struct BigConfig { a: A, b: B, c: C }

fn build() -> BigConfig {
    let mut config = std::mem::MaybeUninit::<BigConfig>::uninit();
    let ptr = config.as_mut_ptr();
    unsafe {
        std::ptr::addr_of_mut!((*ptr).a).write(compute_a());
        std::ptr::addr_of_mut!((*ptr).b).write(compute_b());  // if this panics, `a` above
                                                                 // needs manual unsafe cleanup
        std::ptr::addr_of_mut!((*ptr).c).write(compute_c());
        config.assume_init()
    }
}
```

```metel
@derive(ToRecord, FromRecord)
struct BigConfig { a: A, b: B, c: C }

fun build() -> BigConfig {
    let partial = { a = compute_a() };
    let partial = { ..partial, b = compute_b() };  // if this panics, `partial` is an
                                                   // ordinary, fully-valid record
                                                   // { a: A } — dropped through the
                                                   // same safe machinery as any
                                                   // other value, no manual cleanup
    let partial = { ..partial, c = compute_c() };
    BigConfig::from_record(partial)   // only typechecks once the row exactly matches
                                       // BigConfig's full shape — assume_init()'s runtime
                                       // assertion, made a compile-time fact instead
}
```

**A generic, reusable helper that splits a struct's fields into independent `&mut`
pieces, across a function boundary.** Rust's borrow checker's field-sensitivity is
intra-procedural only. Real code either duplicates the splitting logic inline at every
call site, or reaches for unsafe pointer-cast tricks. This is exactly the motivating gap
behind Rust's own (still unshipped, as of writing) "view types" proposal:

```metel
fun drain_field<row R, name: Symbol, T>(s: &mut { name: T, ..R })
    -> (T, &mut { ..R })
{
    let v = move s.[name];
    (v, s)
}

@derive(ToRecord, FromRecord)
struct Handle { fd: i32, alloc: @a Buffer }

fun example(h: &mut Handle) {
    let view = h.to_record_mut();
    let (buf, rest) = drain_field::<_, "alloc", @a Buffer>(view);
    // `buf: @a Buffer` and `rest: &mut { fd: i32 }` are independently usable —
    // `drain_field` was written once, generically, and works unmodified for any struct
    // that derives ToRecord/FromRecord, not just Handle
}
```

---

## Open Questions

1. Transitive field-usage checking when a `Drop` body calls helper methods (§1) —
   unresolved, no proposal yet.
2. Whether Option C, if adopted, replaces RFC-0071 §7's affine partial-move side-table
   too, or stays linear/record-scoped only — unresolved.
3. §2.1's aliasing-question answer needs a real soundness argument, not just
   unbroken worked examples — tracked as the primary blocker on treating Option C as
   ratified.
4. **New, 2026-07-24. Does Metel want *label polymorphism* — being generic over which
   field, not just over the rest of the row?** §5's `drain_field` assumes it and is the
   only construct in the corpus that does:

   ```metel
   fun drain_field<row R, name: Symbol, T>(s: &mut { name: T, ..R }) -> (T, &mut { ..R })
   { let v = move s.[name]; (v, s) }
   ```

   **Three separate things here do not exist**, checked directly against `grammar.pest`:

   - **`Symbol` is not a kind.** The only `Symbol` in the corpus is RFC-0059's
     compiler-internal `SymbolId`, unrelated. Nothing defines a label kind.
   - **`name: Symbol` does not even mean what it looks like.**
     `generic_param = { ident ~ (":" ~ bound_list)? }`, so it parses as "type parameter
     `name`, bounded by an aspect called `Symbol`" — a *type* variable, not a label. It
     gets a valid-but-wrong reading rather than an error. Note the inconsistency sitting
     in the same parameter list: `<row R>` marks a non-type kind with a **prefix
     keyword**, the pattern this cluster settled on; `<name: Symbol>` tries to mark one in
     bound position.
   - **`s.[name]` does not parse.** `postfix` accepts `.0`, `.ident`, `.ident(…)`,
     `[expr]` and `?`. There is no `.[` form, and bare `[expr]` is the runtime index
     operator, not a compile-time label projection.

   **This is not settled by RFC-0090 §2.1's resolution of row algebra, and the distinction
   matters.** That resolution retires the need for a label *literal* — extension writes
   the label inside a row literal, removal names both halves in an equation. It does not
   provide label *polymorphism*: `where R = { name: T, ..Rest }` still leaves `name`
   ranging over labels. `drain_field` needs the stronger capability, independently.

   **What it would cost:** a label kind (spelled as a prefix keyword, to match `row`), a
   label literal, a record-index-by-label expression form, and typing rules for all three.
   Precedented — PureScript types `Record.delete` as
   `IsSymbol l => Row.Cons l a r1 r2 => Proxy l -> Record r2 -> Record r1`, and Haskell's
   `row-types` is the same shape — but it is the heavy end of row polymorphism, and the
   part Elm dropped.

   **What is at stake if the answer is no:** `drain_field` either specialises per field
   (`drain_alloc`, `drain_token`) or goes away, and **RFC-0109's Motivation needs
   editing** — it cites the generic `drain_field<row R, name, T>` as the "reusable half"
   that records give and Rust's view types cannot, so it is load-bearing for that RFC's
   argument, not merely an illustration.

> **Update 2026-07-18:** RFC-0109 (Self-View Narrowing and Reference-Destructuring
> Patterns) reuses this RFC's `(row, brand)` residual representation directly for a
> second purpose. Its §4 defines named *views* — `view X for Struct { fields }` — as a
> named, non-consuming point in the same `(row, brand)` lattice §2.2 above defines for
> partial-move residuals; its §4.5 splits "does a self-view fit the receiver's row"
> into the ordinary intact-struct case (no dependency on Option C at all) and the
> already-partially-consumed-residual case, which does inherit this RFC's still-open
> §2.1 aliasing question rather than resolving it independently.

---

## References

- RFC-0089 (Linear Types) — the multiplicity lattice and `ToRecord`-based floor this RFC
  extends
- RFC-0090 (Structural Records — Rows and Tiers) — the row/tier machinery (bare-row
  bounds positive and negative, tier 2's `to_record_mut`/`from_record_mut`) this RFC's Option C is built
  entirely from
- RFC-0071 (Ownership and Move Semantics) — §7's blanket partial-move-out-of-`Drop` ban
  this RFC's §1 narrows
- `brand-types.md` — `RcToken`, dividing labor with §1.1's `RcBox` example
- `brand-kind-unification.md` — the `(row, brand)` tag-reuse claim §2.2 depends on
- `reports/substructural-types/linear-types.md` and `structural-records.md` — the
  living design reports this RFC is extracted from
- `reports/strategy/strategic-overview-2026-07-08.md` — classifies this thread as
  paced, paper-only-territory work, not gating anything
- RFC-0109 (Self-View Narrowing and Reference-Destructuring Patterns) — reuses this
  RFC's row-shrink representation for a second purpose; see the Open Questions update
  above

---

## Decision

**Outcome:** *(pending)*
**Target:** unspecified; explicitly not required for RFC-0063 §9 item 5's deadline,
which RFC-0089 (together with RFC-0090's `{ … }` former/tier 2) already satisfies.

*(Decision rationale goes here when the RFC is evaluated.)*
