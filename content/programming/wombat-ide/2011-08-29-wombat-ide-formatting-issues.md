---
title: Wombat IDE - Formatting issues
date: 2011-08-29 05:05:42
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: formatting-issues
---
A minor update related to <a title="Issue 42" href="https://code.google.com/p/wombat-ide/issues/detail?id=42">Issue 42</a> on the Issue Tracker.

Essentially, I want to make everything output as they should in <a title="The SCheme Programming Language" href="http://schemers.org/">Scheme</a> as opposed to how they do in <a title="The Kawa Language Framework" href="http://www.gnu.org/software/kawa/">Kawa</a>/<a title="java.com: Java + You" href="http://java.com/">Java</a>. For each case below, the first option is what we see now and the second is what we should see.

<!--more-->

```scheme
§ "cat"
cat
"cat"

§ #\a
'a'
#\a

§ #t
true
#t

§ #(a b c)
[a, b, c]
#(a b c)

§ (vector "a" "b" "c")
[a, b, c]
#("a" "b" "c")

§ (make-vector 3)
[#!undefined, #!undefined, #!undefined]
#(0 0 0)
```

All but the last one were just a matter of writing a custom (recursive) formatter for the output. The last one requires actually redefining make-vector to default to filling with 0 unless a second parameter is provided, but that shouldn't be difficult.

The new build is r158, available <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>.