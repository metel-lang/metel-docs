---
sidebar_position: 22
---

# Aspect Declaration Properties

> **Gap** GAP-DECLARATIONS-005

An aspect declaration may state properties that replace behaviour the compiler otherwise hardcodes for a named
aspect. The compiler reads them from the aspect's declaration, never from its spelling.

| Property | Meaning | Who may use it |
|---|---|---|
| `declared` | granted to a named type only through its declaration clauses, never by `extend` | any aspect |
| `derivable` | the compiler writes its implementation, so `derives A` is legal | std only |
| `auto` | granted structurally with no entry; a type opts out with a negative impl | std only (reserved) |
| `implicit` | a by-value use of a type satisfying the aspect copies its representation instead of moving | std only |

<!-- doc-example: skip reason="shows a rejected program" -->
```metel
declared aspect Validated;          // a user marker: granted in the declaration of the type

struct Token: Validated { id: i64 }
extend Token: Validated;            // error: Validated is declared; grant it in the declaration
```

A `declared` aspect is [granted only in the declaration](#spec.declarations.aspects.aspect-declaration-properties.legality-1).
Targets with no declaration of their own (primitives, tuples, arrays, anonymous records, references) cannot carry a
clause; impls for them are allowed only in the aspect's defining module. `implicit` is the one property that is a
language semantic and not a constraint: it is [restricted to the standard library](#spec.declarations.aspects.aspect-declaration-properties.legality-2).
Which types satisfy `Copy`, and what the implicit copy does, are specified in [Ownership and Move Semantics](../../ownership/index.md).

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.aspect-declaration-properties.legality-1}

A `declared` aspect is satisfied by a named type only if the type's declaration grants it, through the colon list or `derives`. An `extend T: A` of a `declared` aspect for a named type is an error with a fix-it that moves it into the declaration.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0212](../../../../rfcs/4-implemented/rfc-0212-aspect-declaration-properties.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (4)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDQ1IiwiY29sIjpudWxsLCJjb250YWlucyI6ImlzIGEgYGRlY2xhcmVkYCBhc3BlY3QiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJjb3B5X3N0cnVjdF93aXRoX2Ffd3JpdHRlbl9leHRlbmRfY29weV9pc190MDA0NS5tdGwiLCJzb3VyY2UiOiJjb3B5IHN0cnVjdCBGIHsgbjogaTY0IH1cbmV4dGVuZCBGOiBDb3B5OyAvLyBFUlJPUltUMDA0NV1cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2FzcGVjdHMvY29weV9zdHJ1Y3Rfd2l0aF9hX3dyaXR0ZW5fZXh0ZW5kX2NvcHlfaXNfdDAwNDUubXRsIiwibmFtZSI6ImNvcHlfc3RydWN0X3dpdGhfYV93cml0dGVuX2V4dGVuZF9jb3B5X2lzX3QwMDQ1Lm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDQ1IiwiY29sIjpudWxsLCJjb250YWlucyI6ImlzIGEgYGRlY2xhcmVkYCBhc3BlY3QiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJkZWNsYXJlZF9hc3BlY3RfZXh0ZW5kX29uX2FfbmFtZWRfdHlwZV9pc190MDA0NS5tdGwiLCJzb3VyY2UiOiJkZWNsYXJlZCBhc3BlY3QgVmFsaWRhdGVkO1xuc3RydWN0IFRva2VuIHsgaWQ6IGk2NCB9XG5leHRlbmQgVG9rZW46IFZhbGlkYXRlZDsgLy8gRVJST1JbVDAwNDVdXG5mdW4gbWFpbigpIHt9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9hc3BlY3RzL2RlY2xhcmVkX2FzcGVjdF9leHRlbmRfb25fYV9uYW1lZF90eXBlX2lzX3QwMDQ1Lm10bCIsIm5hbWUiOiJkZWNsYXJlZF9hc3BlY3RfZXh0ZW5kX29uX2FfbmFtZWRfdHlwZV9pc190MDA0NS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImRlY2xhcmVkX2FzcGVjdF9pc19ncmFudGFibGVfZm9yX2FfaGVhZGVybGVzc190eXBlX2luX2l0c19tb2R1bGUubXRsIiwic291cmNlIjoiLy8gUkZDLTAyMTIgc2VjdGlvbiAxOiBhIHR5cGUgd2l0aCBubyBkZWNsYXJhdGlvbiBvZiBpdHMgb3duIGNhbiBiZSBncmFudGVkIGEgZGVjbGFyZWQgYXNwZWN0IGluIHRoZVxuLy8gYXNwZWN0J3MgZGVmaW5pbmcgbW9kdWxlOyB0aGUgYXNwZWN0J3MgcHJvcGVydGllcyBkbyBub3Qgc3RvcCBpdCBiZWluZyBkZWNsYXJlZCBvciB1c2VkIGFzIGEgYm91bmQuXG5kZWNsYXJlZCBhc3BlY3QgVGFnZ2VkIHsgZnVuIHRhZygmc2VsZikgLT4gaTY0OyB9XG5leHRlbmQgaTY0OiBUYWdnZWQgeyBmdW4gdGFnKCZzZWxmKSAtPiBpNjQgeyBzZWxmICsgMSB9IH1cbnB1YiBkZWNsYXJlZCBhc3BlY3QgTWFya2VkO1xuXG5mdW4gdGFnX29mPFQ6IFRhZ2dlZD4oeDogJlQpIC0+IGk2NCB7IHgudGFnKCkgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBhc3NlcnQodGFnX29mKCY0KSA9PSA1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2FzcGVjdHMvZGVjbGFyZWRfYXNwZWN0X2lzX2dyYW50YWJsZV9mb3JfYV9oZWFkZXJsZXNzX3R5cGVfaW5faXRzX21vZHVsZS5tdGwiLCJuYW1lIjoiZGVjbGFyZWRfYXNwZWN0X2lzX2dyYW50YWJsZV9mb3JfYV9oZWFkZXJsZXNzX3R5cGVfaW5faXRzX21vZHVsZS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE0IiwiY29sIjpudWxsLCJjb250YWlucyI6Im9ycGhhbiBpbXBsZW1lbnRhdGlvbiIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGhlbHBlcjo6TWFya2VyO1xuZXh0ZW5kIGk2NDogTWFya2VyOyAvLyBFUlJPUltUMDAxNF1cbmZ1biBtYWluKCkge31cbiJ9LHsibmFtZSI6ImhlbHBlci5tdGwiLCJzb3VyY2UiOiJwdWIgZGVjbGFyZWQgYXNwZWN0IE1hcmtlcjtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9kZWNsYXJlZF9hc3BlY3RfaGVhZGVybGVzc19ncmFudF9vdXRzaWRlX2l0c19tb2R1bGUiLCJuYW1lIjoiZGVjbGFyZWRfYXNwZWN0X2hlYWRlcmxlc3NfZ3JhbnRfb3V0c2lkZV9pdHNfbW9kdWxlIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-declaration-properties.legality-2}

The properties `implicit` and `auto` are accepted only on an aspect declared in the standard library. An `implicit` aspect must refine `Clone` through a `deriving` super-aspect, and at most one `implicit` aspect exists in a program. A violation is an error at the aspect declaration.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0212](../../../../rfcs/4-implemented/rfc-0212-aspect-declaration-properties.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDQ1IiwiY29sIjpudWxsLCJjb250YWlucyI6IndyaXR0ZW4gdHdpY2UiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJhc3BlY3RfcHJvcGVydHlfd3JpdHRlbl90d2ljZV9pc190MDA0NS5tdGwiLCJzb3VyY2UiOiJkZWNsYXJlZCBkZWNsYXJlZCBhc3BlY3QgTWluZTsgLy8gRVJST1JbVDAwNDVdXG5mdW4gbWFpbigpIHt9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9hc3BlY3RzL2FzcGVjdF9wcm9wZXJ0eV93cml0dGVuX3R3aWNlX2lzX3QwMDQ1Lm10bCIsIm5hbWUiOiJhc3BlY3RfcHJvcGVydHlfd3JpdHRlbl90d2ljZV9pc190MDA0NS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDQ1IiwiY29sIjpudWxsLCJjb250YWlucyI6ImFjY2VwdGVkIG9ubHkgb24gYW4gYXNwZWN0IGRlY2xhcmVkIGluIHRoZSBzdGFuZGFyZCBsaWJyYXJ5IiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoiYXV0b19wcm9wZXJ0eV9vbl9hX3VzZXJfYXNwZWN0X2lzX3QwMDQ1Lm10bCIsInNvdXJjZSI6ImF1dG8gYXNwZWN0IE1pbmU7IC8vIEVSUk9SW1QwMDQ1XVxuZnVuIG1haW4oKSB7fVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYXNwZWN0cy9hdXRvX3Byb3BlcnR5X29uX2FfdXNlcl9hc3BlY3RfaXNfdDAwNDUubXRsIiwibmFtZSI6ImF1dG9fcHJvcGVydHlfb25fYV91c2VyX2FzcGVjdF9pc190MDA0NS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDQ1IiwiY29sIjpudWxsLCJjb250YWlucyI6ImFjY2VwdGVkIG9ubHkgb24gYW4gYXNwZWN0IGRlY2xhcmVkIGluIHRoZSBzdGFuZGFyZCBsaWJyYXJ5IiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoiaW1wbGljaXRfcHJvcGVydHlfb25fYV91c2VyX2FzcGVjdF9pc190MDA0NS5tdGwiLCJzb3VyY2UiOiJpbXBsaWNpdCBhc3BlY3QgTWluZTsgLy8gRVJST1JbVDAwNDVdXG5mdW4gbWFpbigpIHt9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9hc3BlY3RzL2ltcGxpY2l0X3Byb3BlcnR5X29uX2FfdXNlcl9hc3BlY3RfaXNfdDAwNDUubXRsIiwibmFtZSI6ImltcGxpY2l0X3Byb3BlcnR5X29uX2FfdXNlcl9hc3BlY3RfaXNfdDAwNDUubXRsIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-declaration-properties.legality-3}

The properties of an aspect are read from its declaration by identity. A re-export, alias or import of the aspect carries them unchanged.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDQ1IiwiY29sIjpudWxsLCJjb250YWlucyI6ImlzIGEgYGRlY2xhcmVkYCBhc3BlY3QiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJtYWluLm10bCIsInNvdXJjZSI6ImltcG9ydCBoZWxwZXI6Ok1hcmtlciBhcyBNYXJrO1xuc3RydWN0IFRva2VuIHsgaWQ6IGk2NCB9XG5leHRlbmQgVG9rZW46IE1hcms7IC8vIEVSUk9SW1QwMDQ1XVxuZnVuIG1haW4oKSB7fVxuIn0seyJuYW1lIjoiaGVscGVyLm10bCIsInNvdXJjZSI6InB1YiBkZWNsYXJlZCBhc3BlY3QgTWFya2VyO1xuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL2RlY2xhcmVkX2FzcGVjdF9hbGlhc19pbXBvcnRfa2VlcHNfaXRzX3Byb3BlcnR5IiwibmFtZSI6ImRlY2xhcmVkX2FzcGVjdF9hbGlhc19pbXBvcnRfa2VlcHNfaXRzX3Byb3BlcnR5In0="></details>
<!-- rfc.py:fixtures:end -->

</details>

---
