# Metel - a new-born exploratory system language

## Introduction

You surely know as well as I do that the world does not need yet another amateur Rust/Zig clone, so let me be totally honest with you: The main reason I built Metel is because I wanted to build my own programming language out of pure curiosity and love for the challenge of building complex systems.

The initial goal was very simple: Build a statically typed, garbage collected, heavily Rust-inspired, and interpreted language. But once I had the base language laid down, the desire to go further than that grew inside of me.

I started to do a go deeper into language design and different ways existing languages solve different problems, inspired by some great articles on language design concepts (https://verdagon.dev/blog/ante-blending-borrowing-rc and https://federicobruzzone.github.io/posts/eter/a-friendly-tour-of-substructural-uniqueness-ownership-and-capabilities-types-and-more.html).

I learned about substructural types, uniqueness types, fractional uniqueness, region types, linear capabilities, effect systems, reference capabilities, and much more. At some point I started to wonder: could I try and mix existing, well-researched language-design concepts and ideas into a genuinely novel and interesting mix?

I am in no way expecting Metel to be a real competitor to enstablished system languages, but I am willing to try my best at designing a language that is worth building.


