---
sidebar_position: 12
---

# Implementing an Aspect

```metel
struct Point {
    x: f64,
    y: f64,
}

aspect Printable {
    fun print(self);
}

extend Point: Printable {
    fun print(self) {
        print("(");
        print(self.x.to_string());
        print(", ");
        print(self.y.to_string());
        println(")");
    }
}

fun main() {
    let p := Point { x = 1.0, y = 2.0 };
    p.print();
}
```

**Aspect implementation method set.** An `extend Type: Aspect` block must define
exactly the methods declared by `Aspect`: every declared method must be present unless it
has a default body, and no additional methods are permitted. Put a type-specific method
that is not part of the aspect in an inherent `extend Type .{ ... }` block; [inherent and
aspect implementations may coexist for the same type](#spec.declarations.aspects.implementing-an-aspect.legality-1).

**Aspect implementation method signatures.** Each implementation method must
conform to the aspect's declaration of that method. The aspect signature is first
[specialized](../variables/record-pattern-bindings.md#spec.declarations.aspects.implementing-an-aspect.legality-12) with
the block's target type for `Self`, its aspect arguments, and its associated-type
definitions; receiver form, ordinary parameter count and types, and result type
must then be equal. The method's generic constraints must be
[structurally equal](../variables/record-pattern-bindings.md#spec.declarations.aspects.implementing-an-aspect.legality-13)
to the aspect method's after normalization — neither weakened nor strengthened —
with record kind part of the comparison. A method that does not conform is
[rejected at its own declaration](../variables/record-pattern-bindings.md#spec.declarations.aspects.implementing-an-aspect.legality-14)
and does not satisfy the aspect.

```metel
aspect CopyOnly { fun pass<T: Copy>(value: T) -> T; }

extend Holder: CopyOnly {
    fun pass<T: Copy>(value: T) -> T { value }   // ok -- identical constraints
    // fun pass<T>(value: T) -> T { value }       // rejected: weakened (T0012)
}

aspect AnyValue { fun keep<T>(value: T) -> T; }

extend Holder: AnyValue {
    fun keep<record T>(value: T) -> T { value }   // rejected: strengthened (T0012)
}
```

> **Gap** GAP-DECLARATIONS-002: a widening, such as a plain `<T>` implementing an aspect's `<record T>`, is rejected as a conservative wrong-no.

**Conditional extend blocks.** An aspect implementation for a
generic type may be conditional on its own type parameters satisfying additional
bounds, written in a `where` clause after the aspect clause (or inline, before the
target type):

```metel
struct Pair<A, B> { first: A, second: B }

extend Pair<A, B>: Printable where A: Printable, B: Printable {
    fun print(self) { ... }
}

// equivalent, inline form:
extend<A: Printable, B: Printable> Pair<A, B>: Printable { ... }
```

`Pair<i64, String>` is `Printable`; `Pair<i64, SomeNonPrintableType>` is not — both
remain constructable, since a struct's own unconditional bounds (above) and an extend
block's conditional bounds are checked independently. The compiler checks a conditional
block's bounds at every point the aspect is required — method call, bound check, impl
selection — not at the block's own declaration site:

```metel
fun print_pair<A: Printable, B: Printable>(p: Pair<A, B>) {
    p.print();   // ok -- conditional impl applies; A: Printable and B: Printable
}

fun use_pair(p: Pair<i64, SomeNonPrintable>) {
    p.print();   // error T0012: Pair<i64, SomeNonPrintable> does not implement
                 //   Printable, because SomeNonPrintable does not implement Printable
}
```

A generic function propagates a conditional extend block to its own callers by stating
the bound explicitly — the compiler never infers which bounds a caller needs:

```metel
fun print_sorted<T: Comparable + Printable>(list: SortedList<T>) {
    list.print();   // ok -- T: Printable, so the conditional extend block applies
}
```

Negative bounds may appear in a conditional `extend` block's `where` clause on the same
terms as positive ones:

```metel
extend<T: !Drop> Container<T>: BulkDrop { ... }
```

**Coherence.** [Two conditional `extend` blocks of the same aspect for the same type are
a coherence error (`T0015`) unless they are provably disjoint](../variables/record-pattern-bindings.md#spec.declarations.aspects.implementing-an-aspect.legality-8). Disjointness is
established by **syntactic negation** only — one block must carry an explicit negative
bound that directly negates a positive bound in the other. The compiler performs no
inference beyond this direct check:

```metel
// Accepted -- T: !Copy directly negates T: Copy; provably disjoint
extend<T: Copy> Wrapper<T>: Serialize { ... }
extend<T: !Copy> Wrapper<T>: Serialize { ... }

// error T0015 -- no direct negation between Clone and Display; not provably disjoint
extend<T: Clone> Wrapper<T>: Serialize { ... }
extend<T: Display> Wrapper<T>: Serialize { ... }
```

A conditional `extend` block and an unconditional `extend` block for the same type
constructor are also a coherence error — the unconditional block already covers every
instantiation the conditional one would. Conditional blocks are subject to the same
orphan rule as unconditional ones (above): the aspect or the type's outermost
constructor must be local.

**Bare-parameter blanket impls.** `extend<T: Bound> T: Aspect` — where the target is
the block's own generic parameter rather than a named struct or enum wrapping it, e.g.
`extend<T: Copy> T: Clone` — is a distinct case from every other example in this
section, which all target a genuine named type (`Pair<A, B>`, `Container<T>`,
`Wrapper<T>`). A bare type parameter has no outermost type constructor for the orphan
rule (below) to check — it isn't declared in any module, including the block's own.
Target-locality is therefore **vacuously unsatisfiable** for this shape: such an extend
is permitted only through the aspect side of the orphan rule, never the target side.

```metel
// std::core — permitted: Clone is local to std::core
extend<T: Copy> T: Clone { fun clone(self: &T) -> T { self } }

// user module — permitted: MyAspect is local here
aspect MyAspect { fun tag(self) -> String; }
extend<T: Copy> T: MyAspect { fun tag(self) -> String { "copyable" } }

// user module — REJECTED (T0014): Display is foreign, and a bare-parameter
// target can never be local, anywhere
extend<T: Copy> T: Display { fun to_string(self) -> String { "?" } }
```

This confines any one aspect's bare-parameter blanket impl to a single module (its own
declaring module, or `std::core` for a built-in aspect) — no separate overlap-detection
mechanism is needed beyond the ordinary rule already stated above (two impls of the
same aspect conflict when some instantiation satisfies both): a competing
bare-parameter blanket from another module can never pass the orphan check in the
first place, and a concrete impl overlapping the blanket (e.g. a type implementing
`Clone` directly while also being `Copy`) is caught by the existing concrete-vs-blanket
overlap rule with no special case.

**Worked example — interaction with equality-constrained bounds.** A conditional
`extend` block's `where` clause accepts the same equality-constrained bound form
Associated Types (above) specifies for ordinary function bounds, since both are stored
and checked as the same `Bound` structure:

```metel
aspect Container { type Item: Display; fun get(self) -> Item; }

struct Wrapper<T> { inner: T }

extend<T: Container<Item = i64>> Wrapper<T>: Printable {
    fun print(self) { println(self.inner.get().to_string()); }
}
```

This composes without any new mechanism: the conditional block's bound-checking (this
section) and the equality-constraint-checking Associated Types already specifies are
the same call-site check, run once per bound in the `where` clause, regardless of
which kind of aspect the bound names.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-1}

An inherent implementation is written `extend Type .{ ... }`; an aspect implementation is
written `extend Type: Aspect .{ ... }`, and both forms may coexist for the same type.

<!-- rfc.py:last_reviewed 7ff6bac2f3c159c0d57a74f61abbe3fcb3000089 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0098](../../../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (6)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijc1X2luaGVyZW50X2Fsb25nc2lkZV9hc3BlY3RfaW1wbC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUG9pbnQgeyB4OiBpNjQgfVxuXG5hc3BlY3QgRGVzY3JpYmUge1xuICAgIGZ1biBkZXNjcmliZSgmc2VsZikgLT4gU3RyaW5nO1xufVxuXG5leHRlbmQgUG9pbnQ6IERlc2NyaWJlIHtcbiAgICBmdW4gZGVzY3JpYmUoJnNlbGYpIC0+IFN0cmluZyB7IHJldHVybiBcInBvaW50XCI7IH1cbn1cblxuZXh0ZW5kIFBvaW50IHtcbiAgICBmdW4gdHdpY2UoJnNlbGYpIC0+IGk2NCB7IHJldHVybiBzZWxmLnggKiAyOyB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBwIDo9IFBvaW50IHsgeCA9IDIxIH07XG4gICAgYXNzZXJ0KHAuZGVzY3JpYmUoKSA9PSBcInBvaW50XCIpO1xuICAgIGFzc2VydChwLnR3aWNlKCkgPT0gNDIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYXNwZWN0cy83NV9pbmhlcmVudF9hbG9uZ3NpZGVfYXNwZWN0X2ltcGwubXRsIiwibmFtZSI6Ijc1X2luaGVyZW50X2Fsb25nc2lkZV9hc3BlY3RfaW1wbC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImJsb2NrX2xvY2FsX2ltcGxfaW5fYV9nZW5lcmljX2Z1bmN0aW9uLm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjMTk3OTogYSB0eXBlIGRlY2xhcmVkIGluIGEgZ2VuZXJpYyBmdW5jdGlvbidzIGJvZHksIHdpdGggYW4gaW1wbCB0aGF0IGhhcyBtZXRob2RzLCBpcyBidWlsdCBvbmNlIGF0XG4vLyBkZWZpbml0aW9uIHRpbWUsIHNvIHRoZSBpbXBsIGlzIHJlZ2lzdGVyZWQgYW5kIGl0cyBtZXRob2RzIHJ1biwgYW5kIHRoZSBib2R5IGlzIGFuYWx5c2VkIChpdCB3YXMgSTAwMDYgYXQgcnVuIHRpbWVcbi8vIGFuZCBJMDAxMSB1bmRlciAtLW1vdmUtY2hlY2spLiBUaGUgaW1wbCBuYW1lcyBub25lIG9mIHRoZSBlbmNsb3NpbmcgZ2VuZXJpY3MsIHNvIGl0IGlzIHRoZSBzYW1lIGZvciBldmVyeSBjYWxsLlxuYXNwZWN0IFNob3cgeyBmdW4gc2hvdygmc2VsZikgLT4gU3RyaW5nOyB9XG5mdW4gcmVuZGVyPFU6IFNob3c+KHg6ICZVKSAtPiBTdHJpbmcgeyB4LnNob3coKSB9XG5cbmZ1biBkaXJlY3Q8VD4oeDogVCkgLT4gU3RyaW5nIHtcbiAgICBzdHJ1Y3QgTCB7IG46IGk2NCB9XG4gICAgZXh0ZW5kIEw6IFNob3cgeyBmdW4gc2hvdygmc2VsZikgLT4gU3RyaW5nIHsgXCJMXCIgfSB9XG4gICAgTCB7IG4gPSAxIH0uc2hvdygpXG59XG5cbmZ1biB0aHJvdWdoX2FfYm91bmQ8VD4oeDogVCwgbjogaTY0KSAtPiBTdHJpbmcge1xuICAgIHN0cnVjdCBMIHsgbjogaTY0IH1cbiAgICBleHRlbmQgTDogU2hvdyB7IGZ1biBzaG93KCZzZWxmKSAtPiBTdHJpbmcgeyBcIkwke3NlbGYubn1cIiB9IH1cbiAgICBsZXQgbCA6PSBMIHsgbiA9IG4gfTtcbiAgICByZW5kZXIoJmwpXG59XG5cbmZ1biBpbl9hX2Nsb3N1cmU8VD4oeDogVCkgLT4gU3RyaW5nIHtcbiAgICBzdHJ1Y3QgTCB7IG46IGk2NCB9XG4gICAgZXh0ZW5kIEw6IFNob3cgeyBmdW4gc2hvdygmc2VsZikgLT4gU3RyaW5nIHsgXCJjbG9zdXJlXCIgfSB9XG4gICAgbGV0IGYgOj0gfGs6IGk2NHwgLT4gU3RyaW5nIHsgTCB7IG4gPSBrIH0uc2hvdygpIH07XG4gICAgZigxKVxufVxuXG5mdW4gdHdvX2Jsb2NrczxUPih4OiBULCBmbGFnOiBib29sZWFuKSAtPiBTdHJpbmcge1xuICAgIGlmIChmbGFnKSB7XG4gICAgICAgIHN0cnVjdCBMIHsgbjogaTY0IH1cbiAgICAgICAgZXh0ZW5kIEw6IFNob3cgeyBmdW4gc2hvdygmc2VsZikgLT4gU3RyaW5nIHsgXCJ5ZXNcIiB9IH1cbiAgICAgICAgcmV0dXJuIEwgeyBuID0gMSB9LnNob3coKTtcbiAgICB9XG4gICAgc3RydWN0IEwgeyBuOiBpNjQgfVxuICAgIGV4dGVuZCBMOiBTaG93IHsgZnVuIHNob3coJnNlbGYpIC0+IFN0cmluZyB7IFwibm9cIiB9IH1cbiAgICBMIHsgbiA9IDIgfS5zaG93KClcbn1cblxuZnVuIGdlbmVyaWNfbG9jYWw8VD4oeDogVCkgLT4gU3RyaW5nIHtcbiAgICBzdHJ1Y3QgVzxVPiB7IHY6IFUgfVxuICAgIGV4dGVuZDxVPiBXPFU+OiBTaG93IHsgZnVuIHNob3coJnNlbGYpIC0+IFN0cmluZyB7IFwiV1wiIH0gfVxuICAgIGxldCB3OiBXPGk2ND4gOj0gVyB7IHYgPSAxIH07XG4gICAgcmVuZGVyKCZ3KVxufVxuXG5mdW4gZGlzcGxheWVkPFQ+KHg6IFQpIC0+IFN0cmluZyB7XG4gICAgc3RydWN0IEwgeyBuOiBpNjQgfVxuICAgIGV4dGVuZCBMOiBEaXNwbGF5IHsgZnVuIHRvX3N0cmluZygmc2VsZikgLT4gU3RyaW5nIHsgXCJMJHtzZWxmLm59XCIgfSB9XG4gICAgbGV0IGwgOj0gTCB7IG4gPSAzIH07XG4gICAgXCIke2x9XCJcbn1cblxuc3RydWN0IEJveDxUPiB7IHY6IFQgfVxuZXh0ZW5kPFQ+IEJveDxUPiB7XG4gICAgZnVuIGxhYmVsKCZzZWxmKSAtPiBTdHJpbmcge1xuICAgICAgICBzdHJ1Y3QgTCB7IG46IGk2NCB9XG4gICAgICAgIGV4dGVuZCBMOiBTaG93IHsgZnVuIHNob3coJnNlbGYpIC0+IFN0cmluZyB7IFwibWV0aG9kXCIgfSB9XG4gICAgICAgIEwgeyBuID0gMSB9LnNob3coKVxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KGRpcmVjdCgxKSA9PSBcIkxcIik7XG4gICAgYXNzZXJ0KHRocm91Z2hfYV9ib3VuZCgxLCA1KSA9PSBcIkw1XCIpO1xuICAgIGFzc2VydCh0aHJvdWdoX2FfYm91bmQoXCJhXCIsIDYpID09IFwiTDZcIik7XG4gICAgYXNzZXJ0KGluX2FfY2xvc3VyZSgxKSA9PSBcImNsb3N1cmVcIik7XG4gICAgYXNzZXJ0KHR3b19ibG9ja3MoMSwgdHJ1ZSkgPT0gXCJ5ZXNcIik7XG4gICAgYXNzZXJ0KHR3b19ibG9ja3MoMSwgZmFsc2UpID09IFwibm9cIik7XG4gICAgYXNzZXJ0KGdlbmVyaWNfbG9jYWwoMSkgPT0gXCJXXCIpO1xuICAgIGFzc2VydChkaXNwbGF5ZWQoMSkgPT0gXCJMM1wiKTtcbiAgICBhc3NlcnQoQm94IHsgdiA9IDEgfS5sYWJlbCgpID09IFwibWV0aG9kXCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYXNwZWN0cy9ibG9ja19sb2NhbF9pbXBsX2luX2FfZ2VuZXJpY19mdW5jdGlvbi5tdGwiLCJuYW1lIjoiYmxvY2tfbG9jYWxfaW1wbF9pbl9hX2dlbmVyaWNfZnVuY3Rpb24ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImJsb2NrX2xvY2FsX2ltcGxfd2l0aF9tZXRob2RzLm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjMTk3MzogYW4gaW1wbCB3aXRoIGhhbmQtd3JpdHRlbiBtZXRob2RzIHdyaXR0ZW4gaW4gYSBmdW5jdGlvbiBib2R5IGZvciBhIHR5cGUgZGVjbGFyZWQgdGhlcmUgaXNcbi8vIHJlY29yZGVkIGFuZCBpdHMgbWV0aG9kcyBydW46IGEgZGlyZWN0IGNhbGwsIGFuIGluaGVyZW50IG1ldGhvZCByZWFkaW5nIGBzZWxmYCwgYSBjYWxsIHRocm91Z2ggYSBib3VuZCwgYERpc3BsYXlgXG4vLyB1c2VkIGJ5IGludGVycG9sYXRpb24sIGFuZCBhIGJvZHkgdGhhdCBpcyBlbnRlcmVkIG1vcmUgdGhhbiBvbmNlLlxuYXNwZWN0IFNob3cgeyBmdW4gc2hvdygmc2VsZikgLT4gU3RyaW5nOyB9XG5mdW4gcmVuZGVyPFQ6IFNob3c+KHg6ICZUKSAtPiBTdHJpbmcgeyB4LnNob3coKSB9XG5cbmZ1biBsYWJlbChuOiBpNjQpIC0+IFN0cmluZyB7XG4gICAgc3RydWN0IEwgeyBuOiBpNjQgfVxuICAgIGV4dGVuZCBMIHsgZnVuIGdldCgmc2VsZikgLT4gaTY0IHsgc2VsZi5uIH0gfVxuICAgIGV4dGVuZCBMOiBTaG93IHsgZnVuIHNob3coJnNlbGYpIC0+IFN0cmluZyB7IFwiTFwiICsgc2VsZi5nZXQoKS50b19zdHJpbmcoKSB9IH1cbiAgICBleHRlbmQgTDogRGlzcGxheSB7IGZ1biB0b19zdHJpbmcoJnNlbGYpIC0+IFN0cmluZyB7IFwiPFwiICsgc2VsZi5zaG93KCkgKyBcIj5cIiB9IH1cbiAgICBsZXQgbCA6PSBMIHsgbiA9IG4gfTtcbiAgICBhc3NlcnQoXCIke2x9XCIgPT0gXCI8TCR7bn0+XCIpO1xuICAgIHJlbmRlcigmbClcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgc3RydWN0IEsgeyBuOiBpNjQgfVxuICAgIGV4dGVuZCBLOiBTaG93IHsgZnVuIHNob3coJnNlbGYpIC0+IFN0cmluZyB7IFwiS1wiIH0gfVxuICAgIGFzc2VydChLIHsgbiA9IDEgfS5zaG93KCkgPT0gXCJLXCIpO1xuICAgIGFzc2VydChyZW5kZXIoJksgeyBuID0gMiB9KSA9PSBcIktcIik7XG4gICAgYXNzZXJ0KGxhYmVsKDEpID09IFwiTDFcIik7XG4gICAgYXNzZXJ0KGxhYmVsKDIpID09IFwiTDJcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9hc3BlY3RzL2Jsb2NrX2xvY2FsX2ltcGxfd2l0aF9tZXRob2RzLm10bCIsIm5hbWUiOiJibG9ja19sb2NhbF9pbXBsX3dpdGhfbWV0aG9kcy5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gUkZDLTAwNjAgXHUwMGE3NTogYSBuZWdhdGl2ZSBpbXBsIGJlYXRzIGEgYmxhbmtldCBwb3NpdGl2ZSBpbXBsIGZvciB0aGUgc2FtZVxuLy8gY29uY3JldGUgdHlwZSAtLSBwZXJtaXR0ZWQgKG5vIFQwMDE1KSwgYW5kIHRoZSBuZWdhdGl2ZSBpbXBsIHdpbnMgZm9yIGJvdW5kXG4vLyBzYXRpc2ZhY3Rpb24gKEZvbzxpNjQ+OiAhTWFya2VyIGhvbGRzKS5cblxuYXNwZWN0IE1hcmtlciB7XG4gICAgZnVuIG1hcmsoc2VsZikgLT4gU3RyaW5nO1xufVxuXG5zdHJ1Y3QgRm9vPFQ+IHtcbiAgICB2YWx1ZTogVCxcbn1cblxuZXh0ZW5kPFQ+IEZvbzxUPjogTWFya2VyIHtcbiAgICBmdW4gbWFyayhzZWxmKSAtPiBTdHJpbmcgeyByZXR1cm4gXCJibGFua2V0XCI7IH1cbn1cblxuZXh0ZW5kIEZvbzxpNjQ+OiAhTWFya2VyO1xuXG5mdW4gbmVlZHNfbm90X21hcmtlcjxVOiAhTWFya2VyPih4OiBVKSB7fVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgZiA6PSBGb28geyB2YWx1ZSA9IDUgfTtcbiAgICBuZWVkc19ub3RfbWFya2VyKGYpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYXNwZWN0cy9uZWdhdGl2ZV9pbXBsX292ZXJyaWRlc19ibGFua2V0X2ltcGxfcGVybWl0dGVkIiwibmFtZSI6Im5lZ2F0aXZlX2ltcGxfb3ZlcnJpZGVzX2JsYW5rZXRfaW1wbF9wZXJtaXR0ZWQifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InYwXzE2XzBfYmxvY2tfbG9jYWxfaW1wbF93aXRoX3NwcmVhZHNfdHVwbGVzX2FuZF9jb3B5X2Z1bmN0aW9ucy5tdGwiLCJzb3VyY2UiOiIvLyB2MC4xNi4wIGludGVncmF0aW9uOiBhIGJsb2NrLWxvY2FsIGFzcGVjdCBpbXBsIHggcmVjb3JkIHNwcmVhZCB4IHR1cGxlcyBhcyByb3dzIHggdGhlIGNvcHkgZnVuY3Rpb24tdHlwZSBxdWFsaWZpZXIuXG5hc3BlY3QgRGVzY3JpYmUgeyBmdW4gZGVzY3JpYmUoJnNlbGYpIC0+IGk2NDsgfVxuZnVuIG1haW4oKSB7XG4gICAgc3RydWN0IExvY2FsIHsgbjogaTY0IH1cbiAgICBleHRlbmQgTG9jYWw6IERlc2NyaWJlIHsgZnVuIGRlc2NyaWJlKCZzZWxmKSAtPiBpNjQgeyBzZWxmLm4gfSB9XG4gICAgbGV0IHIgOj0gLnsgLmwgPSBMb2NhbCB7IG4gPSAxIH0sIC5rID0gMCB9O1xuICAgIGxldCBzIDo9IC57IC4uciwgLmsgPSA1IH07XG4gICAgYXNzZXJ0KHMubC5kZXNjcmliZSgpID09IDEpO1xuICAgIGFzc2VydChzLmsgPT0gNSk7XG4gICAgbGV0IHQgOj0gKExvY2FsIHsgbiA9IDIgfSwgMyk7XG4gICAgYXNzZXJ0KHQuMC5kZXNjcmliZSgpID09IDIpO1xuICAgIGxldCBpbmM6IGNvcHkgfGk2NHwgLT4gaTY0IDo9IHx4fCB7IHggKyAxIH07XG4gICAgbGV0IHUgOj0gLnsgLmYgPSBpbmMsIC5sID0gTG9jYWwgeyBuID0gMyB9IH07XG4gICAgYXNzZXJ0KCh1LmYpKDEpID09IDIpO1xuICAgIGFzc2VydCh1LmwuZGVzY3JpYmUoKSA9PSAzKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2ludGVncmF0aW9uL3YwXzE2XzBfYmxvY2tfbG9jYWxfaW1wbF93aXRoX3NwcmVhZHNfdHVwbGVzX2FuZF9jb3B5X2Z1bmN0aW9ucy5tdGwiLCJuYW1lIjoidjBfMTZfMF9ibG9ja19sb2NhbF9pbXBsX3dpdGhfc3ByZWFkc190dXBsZXNfYW5kX2NvcHlfZnVuY3Rpb25zLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InYwXzE2XzBfc3ByZWFkc19kb3R0ZWRfbGFiZWxzX25lZ2F0aXZlX2JvdW5kc19hbmRfY29weV9mbG93cy5tdGwiLCJzb3VyY2UiOiIvLyB2MC4xNi4wIGludGVncmF0aW9uOiBkb3R0ZWQgbGFiZWxzIHggbmVnYXRpdmUgcm93IGJvdW5kcyBvdmVyIHJlY29yZHMgYW5kIHR1cGxlcyB4IHNwcmVhZCB0aGVuIHJlcGxhY2UgeCBmbG93IGFyZ3VtZW50cyBhbmRcbi8vIGNvcHkoVCkgeCBkZXJpdmVkIENsb25lIHggYSBibG9jay1sb2NhbCBpbXBsIHggYSBjb3B5IGZ1bmN0aW9uIHgga2V5d29yZCBjYWxscyB4IGEgQ29weSByZXNpZHVhbCB4IHVuZGVjaWRlZCBvd25lcnNoaXAuXG5hc3BlY3QgRGVzY3JpYmUgeyBmdW4gZGVzY3JpYmUoJnNlbGYpIC0+IGk2NDsgfVxuY29weShUKSBzdHJ1Y3QgQm94ZWQ8VD4geyB2YWx1ZTogVCB9XG5zdHJ1Y3QgV3JhcHBlcjxUPiBkZXJpdmVzIENsb25lKFQpLCBDb3B5KFQpIHsgdmFsdWU6IFQgfVxuY29weSBzdHJ1Y3QgVGFnZ2VkPFQ+IHsgbjogaTY0LCB2YWx1ZTogVCB9XG5cbmZ1biBzY2FsZShieTogaTY0LCB4OiBpNjQpIC0+IGk2NCB7IGJ5ICogeCB9XG5mdW4gYXBwbHk8cmVjb3JkIFI6IC57IC5mOiBjb3B5IHxpNjR8IC0+IGk2NCwgIS5zZWNyZXQsIC4uIH0+KHI6IFIsIHg6IGk2NCkgLT4gaTY0IHsgKHIuZikoeCkgfVxuZnVuIGZpcnN0PHJlY29yZCBSOiAueyAuMDogaTY0LCAhLnNlY3JldCwgLi4gfT4ocjogUikgLT4gaTY0IHsgci4wIH1cbmZ1biByZWdlbjxUOiBDb3B5PihiOiBCb3hlZDxUPiwgcjogLnsgLms6IGk2NCB9KSAtPiBpNjQge1xuICAgIGxldCBhIDo9IC57IC4uciwgLmIgPSBiIH07XG4gICAgbGV0IGMgOj0gLnsgLi5yLCAuYiA9IGIgfTtcbiAgICBhLmsgKyBjLmtcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgc3RydWN0IExvY2FsIHsgbjogaTY0IH1cbiAgICBleHRlbmQgTG9jYWw6IERlc2NyaWJlIHsgZnVuIGRlc2NyaWJlKCZzZWxmKSAtPiBpNjQgeyBzZWxmLm4gfSB9XG4gICAgbGV0IGluYzogY29weSB8aTY0fCAtPiBpNjQgOj0gfHh8IHsgeCArIDEgfTtcbiAgICBsZXQgciA6PSAueyAuZiA9IGluYywgLnAgPSBCb3hlZCB7IHZhbHVlID0gMSB9LCAudyA9IFdyYXBwZXIgeyB2YWx1ZSA9IDIgfSwgLmsgPSAwIH07XG4gICAgbGV0IHMgOj0gLnsgLi5yLCAuayA9IDUgfTtcbiAgICBsZXQgdCA6PSAueyAuLnMsIC53ID0gV3JhcHBlciB7IHZhbHVlID0gOSB9IH07XG4gICAgYXNzZXJ0KGFwcGx5KHQsIHNjYWxlKGJ5ID0gMiwgeCA9IDMpKSA9PSA3KTtcbiAgICBsZXQgYyA6PSB0LncuY2xvbmUoKTtcbiAgICBhc3NlcnQoYy52YWx1ZSA9PSA5KTtcbiAgICBhc3NlcnQoZmlyc3QoKDQsIFwic1wiKSkgPT0gNCk7XG4gICAgbGV0IHUgOj0gLnsgLi5yLCAubCA9IExvY2FsIHsgbiA9IDMgfSB9O1xuICAgIGFzc2VydCh1LmwuZGVzY3JpYmUoKSA9PSAzKTtcbiAgICBhc3NlcnQocmVnZW4oQm94ZWQgeyB2YWx1ZSA9IDEgfSwgLnsgLmsgPSAyIH0pID09IDQpO1xuICAgIGxldCB3MiA6PSBUYWdnZWQgeyBuID0gMSwgdmFsdWUgPSBcInNcIiB9O1xuICAgIGxldCBtb3ZlZCA6PSB3Mi52YWx1ZTtcbiAgICBsZXQgYSA6PSB3MjtcbiAgICBsZXQgYiA6PSB3MjtcbiAgICBhc3NlcnQoYS5uICsgYi5uID09IDIpO1xuICAgIGFzc2VydChtb3ZlZCA9PSBcInNcIik7XG4gICAgdmFyIHczIDo9IFRhZ2dlZCB7IG4gPSAxLCB2YWx1ZSA9IFwidFwiIH07XG4gICAgbGV0IHRha2VuIDo9IHczLnZhbHVlO1xuICAgIHczLm4gPSA1O1xuICAgIGxldCB3NCA6PSB3MztcbiAgICBhc3NlcnQodzQubiArIHczLm4gPT0gMTApO1xuICAgIGFzc2VydCh0YWtlbiA9PSBcInRcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9pbnRlZ3JhdGlvbi92MF8xNl8wX3NwcmVhZHNfZG90dGVkX2xhYmVsc19uZWdhdGl2ZV9ib3VuZHNfYW5kX2NvcHlfZmxvd3MubXRsIiwibmFtZSI6InYwXzE2XzBfc3ByZWFkc19kb3R0ZWRfbGFiZWxzX25lZ2F0aXZlX2JvdW5kc19hbmRfY29weV9mbG93cy5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>
