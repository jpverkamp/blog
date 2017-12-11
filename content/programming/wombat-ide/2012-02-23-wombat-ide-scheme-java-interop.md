---
title: Wombat IDE - Scheme/Java Interop
date: 2012-02-23 04:55:12
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: wombat-ide-schemejava-interop
---
In the last few days I've managed to get a version of Scheme/Java interoperability working where Scheme code can call to Java using a side channel alongside the normal communication with the host Wombat process.

<!--more-->

Essentially, the calling from Scheme to Java uses this macro:

```scheme
(library (wombat java)
  (export call-to-java)
  (import (chezscheme))

  (define-syntax call-to-java
    (syntax-rules ()
      [(_ n a* ...)
       (let ()
         (printf "|!~s~a|!" 'n
           (apply string-append
             (map (lambda (a) (format " ~a" a))
               (list a* ...))))
         (let ([result (read)])
           (if (and (not (null? result)) (eq? (car result) 'exception))
               (apply error (cdr result))
               result)))])))
```

Then, to call the function `fact(5)` in Java (if it's been defined), you would just need to do this:

```scheme
(call-to-java fact 5)
```

Then the Java end of things will take over, eventually sending back` (120)` (the interop code always returns a list).

Using this, I've managed to implement `read-image`, `write-image`, and `draw-image` with the same [Image API]({{< ref "2011-08-27-wombat-ide-c211-tree-and-image-libraries.md" >}}).

If you want to switch over to the new versions of Wombat, you can get it <a title="Wombat Launcher Download" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>. You should have at least version 2.54.6.