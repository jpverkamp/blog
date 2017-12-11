---
title: Wombat IDE - A ray of Hope
date: 2011-08-25 05:05:05
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: a-ray-of-hope
---
Since I moved to <a title="The Kawa Language Framework" href="http://www.gnu.org/software/kawa/">Kawa</a>, I've been having an issue with maintaining the state between calls to the interpreter. Everything works fine when I load and run an entire file at once (for example when loading the options files or actually debugging my own code), but when I try to run individual lines of code to add custom bindings, it doesn't work.

<!--more-->

So when I run this:

```java
Scheme kawa = new Scheme();
kawa.eval("(define add1 (lambda (n) (+ n 1)))");
```

It should work, but when I try to use the new code:

```java
Object result = kawa.eval("(add1 5)");
```

I get a NoSuchFieldError. I could use either `kawa.defineFunction(...)` or `kawa.eval("load \"...\")")`, but neither of those is optimal. After hacking around on it for longer than I can to admit, I finally just asked on the Kawa mailing list. <a title="Original email " href="http://sourceware.org/ml/kawa/2011-q3/msg00024.html">Here</a> is my original question, and <a title="First response" href="http://sourceware.org/ml/kawa/2011-q3/msg00025.html">here</a> is the original response from Jamison Hope (ergo the pun) and <a title="Second reply" href="http://sourceware.org/ml/kawa/2011-q3/msg00026.html">another</a> from Per Bothner.

It turns out that I'd actually stumbled upon a bug in <a title="The Kawa Language Framework" href="http://www.gnu.org/software/kawa/">Kawa</a> itself that the one argument version of `eval` (without an Environment specified) was generating Java code with duplicate class names which eventually ended up causing my error. Per checked in some fixes impressively quickly to work around it and even before then I ended up switching to the two argument version of `eval` so that I could otherwise manipulate the Environment object. Problem solved.

The new build is r118, available <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>.