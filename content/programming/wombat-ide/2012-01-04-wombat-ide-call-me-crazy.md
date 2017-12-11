---
title: Wombat IDE - Call me crazy...
date: 2012-01-04 04:55:32
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
...but I'm working on my own implementation of Scheme in Java. Don't get me wrong, Kawa has been great for what it was, but there are just enough things that are just slightly off that I want to make the change.

Essentially, it all comes down to the fact that the autograder and other tools still run on Chez Scheme. Over the semester, there have been an increasing number of problems where the two don't quite agree and so there has to be special cases done by hand. Optimally, I would like Wombat to have 100% compatibility with Chez Scheme (at least in the parts that the students use), but I don't think that I'm going to be able to get there with what I'm doing. There's already about 1000 lines of code to make them work better together and it's only likely to get longer. At some point, I might as well just write my own Scheme. So here goes!

<!--more-->

I started work on 26 December and since then, I've:

* Created a new project next to the IDE project to keep the code separate
* Implemented Scheme versions of all of the different kinds of values specified in R6RS, including the full numeric tower (integers, real numbers, complex numbers, etc). Most of it is built directly on Java code, but some of it is more complicated.
* Implemented a trampolining style of continuations that can avoid the problems I was having with the Java stack, then switched a system based on three stacks (a CLS machine) for the same but ease of implementation
* Added an initial parser and evaluator with some basic interpreter code
* Added an easily extensible framework for literal parsers (with add-ins for all of the current literal values)
* Built in detailed error messages, including line and column numbers and details on surrounding objects

After that, I've added in functions from the following categories:

* Boolean functions
* Character functions
* Control features other than `call/cc` (which I'm likely not to do)
* Equivalence predicates`eq?`, `eqv?`, and `equal?`
* `eval`
* Basic error handling
* cons, car, and cdr
* `lambda`
* `if`
* `set!` and `define` (long form or short form for functions, including zero argument functions)

It's a heck of a start, but there's still a long way to go. In particular, I still need all of the mathematical functions which are going to be a pain and a half to go about and a large number of other categories, such as string functions and I/O. We'll see how long I manage to keep going on this without going crazy.