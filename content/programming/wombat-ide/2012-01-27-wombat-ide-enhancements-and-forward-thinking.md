---
title: Wombat IDE - Enhancements and forward thinking
date: 2012-01-27 04:55:11
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
A few minor enhancements with the new Petite-based builds:

* Start case sensitive by default
* Added a library directory in preparation for the new C211 libraries
* Added code to prevent gensym printing (makes records more readable in general)
* Re-added the C211 tree library (except for draw-tree), it's pure Scheme but the API has[ remained the same]({{< ref "2011-08-27-wombat-ide-c211-tree-and-image-libraries.md" >}})

I still haven't pushed an official build for the students to actually use, but we're getting closer. I think by the time that the students get to the midterm or so, we should be ready to switch over.

&nbsp;