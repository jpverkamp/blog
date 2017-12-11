---
title: Wombat IDE - A bug fix and a timing function
date: 2011-11-03 04:55:39
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
First, a bug fix in `leaf?`. It now does what it's actually supposed to and return `#t` if and only if the objust is a tree with both subtrees satisfying `empty-tree?`.

Second, `cpu-time` has been redefined to only count time spent on actual processing (and not on output / Java wrapper code) while the old functionality has been renamed to the function `real-time`.

Small and simple, but it's still worth a new version. <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/ ">1.306.1</a>.