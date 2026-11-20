---
sidebar_position: 2
---

# Variables

## Immutable Bindings

```metel
fun main() -> i64 {
    let x := 42;
    let name: String := "Vlad";
    if (name == "Vlad") { return x; }
    return 0;
}
```

`let` bindings [cannot be reassigned and must always be initialized](index.md#spec.declarations.variables.immutable-bindings.legality-1). Mutability lives entirely on the binding — a `let` binding is immutable regardless of what value it holds. This means:

So `x = newValue` (reassignment), `x.field = value` (field assignment through an immutable binding) and `&var x` (taking a mutable reference to an immutable binding) are all [rejected](index.md#spec.declarations.variables.immutable-bindings.legality-1): all three forms require `var`.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.variables.immutable-bindings.legality-1}

A `let` binding must be initialized with the `:=` separator and cannot be assigned
after initialization. `:=` is the sole separator that introduces a kept binding; the
plain `=` spelling is a parse error.

<!-- rfc.py:last_reviewed 6fecc8dcbfdd36500a77b2f6139e5f5ef970ce10 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfMTRfbGVnYWN5X2VxdWFsc19iaW5kaW5nX3NlcGFyYXRvci5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDEzNjogYGxldGAvYHZhcmAgZGVjbGFyYXRpb25zIGFuZCBhc3NvY2lhdGVkLXR5cGVcbi8vIGRlZmluaXRpb24gdXNlIGA6PWAgKFJGQy0wMTgzIG1vdmVkIHBsYWluIHJlYXNzaWdubWVudCBiYWNrIHRvIGA9YCkuIFRoZSBvbGQgYD1gIHNlcGFyYXRvciBpcyBhIGhhcmQgcGFyc2UgZXJyb3IgXHUyMDE0IG5vIGFsaWFzLlxuLy8gKENvbXBvdW5kIGArPWAgZXRjLiBhbmQgc3RydWN0LWZpZWxkIGA9YCBhcmUgdW5hZmZlY3RlZDsgc2VlIG5lZ18xNS4pXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgeCA9IDE7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3BhcnNpbmcvbmVnXzE0X2xlZ2FjeV9lcXVhbHNfYmluZGluZ19zZXBhcmF0b3IubXRsIiwibmFtZSI6Im5lZ18xNF9sZWdhY3lfZXF1YWxzX2JpbmRpbmdfc2VwYXJhdG9yLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA2IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjMiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTRfbmVnXzA1X2NvbXBvdW5kX2Fzc2lnbl90b19sZXQubXRsIiwic291cmNlIjoiLy8gQ29tcG91bmQgYXNzaWdubWVudCB0byBhbiBpbW11dGFibGUgYmluZGluZyBpcyBUMDAwNiwgc2FtZSBhcyBwbGFpbiBhc3NpZ24uXG5sZXQgbjogaTY0IDo9IDEwO1xubiArPSA1OyAvLyBFUlJPUltUMDAwNl1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2Z1bmN0aW9ucy9zdGFnZTRfbmVnXzA1X2NvbXBvdW5kX2Fzc2lnbl90b19sZXQubXRsIiwibmFtZSI6InN0YWdlNF9uZWdfMDVfY29tcG91bmRfYXNzaWduX3RvX2xldC5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

## Mutable Bindings

```metel
fun main() -> i64 {
    var counter := 0;
    counter = counter + 1;
    counter += 1;
    return counter;
}
```

`var` bindings [can be reassigned and also must be initialized at declaration](#spec.declarations.variables.mutable-bindings.legality-1). Compound assignment operators `+=`, `-=`, `*=`, `/=`, `%=` are supported.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.variables.mutable-bindings.legality-1}

A `var` binding must be initialized with the `:=` separator and may be assigned after
initialization with `=`; `var` is the mutable binding spelling. `:=` introduces a name and `=`
assigns to an existing place; the compound assignment operators `+=`, `-=`, `*=`,
`/=`, `%=` keep their spelling. The bare `=` spelling for a `var` initializer, and `:=` for a
reassignment, are parse errors.

<!-- rfc.py:last_reviewed 6fecc8dcbfdd36500a77b2f6139e5f5ef970ce10 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md), [rfc-0098](../../../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md), [rfc-0136](../../../../rfcs/4-implemented/rfc-0136-walrus-for-kept-bindings.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (4)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjE2X2Zvcl9sb29wLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIEJhc2ljIGNvdW50aW5nLlxuICAgIHZhciBzdW0gOj0gMDtcbiAgICBmb3IgKHZhciBpIDo9IDA7IGkgPCA1OyBpICs9IDEpIHsgc3VtICs9IGk7IH1cbiAgICBhc3NlcnQoc3VtID09IDEwKTtcbiAgICAvLyBCcmVhayBleGl0cyB0aGUgbG9vcC5cbiAgICB2YXIgY291bnQgOj0gMDtcbiAgICBmb3IgKHZhciBpIDo9IDA7IGkgPCAxMDA7IGkgKz0gMSkge1xuICAgICAgICBpZiAoaSA9PSA1KSB7IGJyZWFrOyB9XG4gICAgICAgIGNvdW50ICs9IDE7XG4gICAgfVxuICAgIGFzc2VydChjb3VudCA9PSA1KTtcbiAgICAvLyBDb250aW51ZSBzdGlsbCBleGVjdXRlcyB0aGUgc3RlcCBleHByZXNzaW9uLlxuICAgIHZhciBjMiA6PSAwO1xuICAgIGZvciAodmFyIGkgOj0gMDsgaSA8IDU7IGkgKz0gMSkge1xuICAgICAgICBpZiAoaSA9PSAyKSB7IGNvbnRpbnVlOyB9XG4gICAgICAgIGMyICs9IDE7XG4gICAgfVxuICAgIGFzc2VydChjMiA9PSA0KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2NvbnRyb2xfZmxvdy8xNl9mb3JfbG9vcC5tdGwiLCJuYW1lIjoiMTZfZm9yX2xvb3AubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImFzc2lnbm1lbnRfb3BlcmF0b3JzX2luX3N0YXRlbWVudF9wb3NpdGlvbnMubXRsIiwic291cmNlIjoiLy8gUkZDLTAxODM6IHBsYWluIGA9YCBhbmQgdGhlIGNvbXBvdW5kIG9wZXJhdG9ycyBhc3NpZ24gaW4gYSBibG9jayBzdGF0ZW1lbnQsIGEgbWF0Y2ggYXJtIGFuZCBhIGBmb3JgXG4vLyBoZWFkZXIncyB1cGRhdGUgY2xhdXNlOyBgOj1gIGludHJvZHVjZXMgbmFtZXMgYW5kIGlzIHVuY2hhbmdlZDsgYGYoeCA9IDEpYCBpcyBhIGtleXdvcmQgYXJndW1lbnQuXG5mdW4gc2NhbGUoYnk6IGk2NCkgLT4gaTY0IHsgYnkgKiAyIH1cblxuZnVuIG1haW4oKSB7XG4gICAgdmFyIG4gOj0gMTA7XG4gICAgbiA9IG4gKyAxO1xuICAgIG4gKz0gMTtcbiAgICBuIC09IDI7XG4gICAgbiAqPSAzO1xuICAgIG4gLz0gMjtcbiAgICBuICU9IDc7XG4gICAgYXNzZXJ0KG4gPT0gMSk7XG5cbiAgICB2YXIgeHMgOj0gWzAsIDAsIDBdO1xuICAgIHhzWzFdID0gNTtcbiAgICBhc3NlcnQoeHNbMV0gPT0gNSk7XG5cbiAgICB2YXIgc3VtIDo9IDA7XG4gICAgZm9yICh2YXIgaSA6PSAwOyBpIDwgNDsgaSA9IGkgKyAxKSB7IHN1bSArPSBpOyB9XG4gICAgYXNzZXJ0KHN1bSA9PSA2KTtcbiAgICBmb3IgKHZhciBqIDo9IDA7IGogPCA0OyBqICs9IDIpIHsgc3VtICs9IDE7IH1cbiAgICBhc3NlcnQoc3VtID09IDgpO1xuXG4gICAgYXNzZXJ0KHNjYWxlKGJ5ID0gMykgPT0gNik7XG4gICAgbGV0IGxvY2FsIDo9IDQ7XG4gICAgYXNzZXJ0KGxvY2FsID09IDQpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9wYXJzaW5nL2Fzc2lnbm1lbnRfb3BlcmF0b3JzX2luX3N0YXRlbWVudF9wb3NpdGlvbnMubXRsIiwibmFtZSI6ImFzc2lnbm1lbnRfb3BlcmF0b3JzX2luX3N0YXRlbWVudF9wb3NpdGlvbnMubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfMTRfbGVnYWN5X2VxdWFsc19iaW5kaW5nX3NlcGFyYXRvci5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDEzNjogYGxldGAvYHZhcmAgZGVjbGFyYXRpb25zIGFuZCBhc3NvY2lhdGVkLXR5cGVcbi8vIGRlZmluaXRpb24gdXNlIGA6PWAgKFJGQy0wMTgzIG1vdmVkIHBsYWluIHJlYXNzaWdubWVudCBiYWNrIHRvIGA9YCkuIFRoZSBvbGQgYD1gIHNlcGFyYXRvciBpcyBhIGhhcmQgcGFyc2UgZXJyb3IgXHUyMDE0IG5vIGFsaWFzLlxuLy8gKENvbXBvdW5kIGArPWAgZXRjLiBhbmQgc3RydWN0LWZpZWxkIGA9YCBhcmUgdW5hZmZlY3RlZDsgc2VlIG5lZ18xNS4pXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgeCA9IDE7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3BhcnNpbmcvbmVnXzE0X2xlZ2FjeV9lcXVhbHNfYmluZGluZ19zZXBhcmF0b3IubXRsIiwibmFtZSI6Im5lZ18xNF9sZWdhY3lfZXF1YWxzX2JpbmRpbmdfc2VwYXJhdG9yLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfMTVfbGVnYWN5X2VxdWFsc19yZWFzc2lnbm1lbnQubXRsIiwic291cmNlIjoiLy8gUkZDLTAxODM6IGA6PWAgb25seSBpbnRyb2R1Y2VzIGEgbmFtZSwgc28gaXQgaXMgbm90IHJlYXNzaWdubWVudC4gYHggOj0gMTtgIHdoZXJlIGB4YCBpcyBub3QgYmVpbmdcbi8vIGRlY2xhcmVkIGlzIGFuIG9yZGluYXJ5IHBhcnNlIGVycm9yLCB3aXRoIG5vIHRhaWxvcmVkIG1lc3NhZ2UuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgeCA6PSAwO1xuICAgIHggOj0gMTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvcGFyc2luZy9uZWdfMTVfbGVnYWN5X2VxdWFsc19yZWFzc2lnbm1lbnQubXRsIiwibmFtZSI6Im5lZ18xNV9sZWdhY3lfZXF1YWxzX3JlYXNzaWdubWVudC5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>
