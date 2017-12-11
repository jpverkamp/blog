---
title: Wombat IDE - Bug fixes, memory issues, and screen sharing
date: 2011-09-28 04:55:20
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
A bit of a bigger update today, bringing the version number up to <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">r213</a>.

First, bug fixes:

* Removed visible references to Java, replacing class names in errors
* Fixed an issue related to hanging on non-procedure errors
* Fix for `even?` and `odd?` to correctly deal with both Java and Kawa numbers
* Added `trace-define`
* Increased stack size to delay infinite loop errors (so that larger code that isn't actually an infinite loop can run)
* Do not format after `#!eof`
* Clear REPL history reset

In addition, I've started working on a feature that I've been hoping to add for a while: screen sharing. Essentially, I'm hoping to add something like Google Docs where two or more users can edit a shared file. Since the C211 labs are always run with pair programming, this will allow students to work on the same code at the same time without constantly switching the keyboard. Unfortunately, it isn't quite working yet, but I'm hopeful.