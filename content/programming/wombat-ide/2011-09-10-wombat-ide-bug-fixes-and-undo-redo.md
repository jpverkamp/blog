---
title: Wombat IDE - Bug fixes and undo/redo
date: 2011-09-10 04:55:42
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: bug-fixes-and-undoredo
---
Two minor bug fixes:

* Fixed the behavior of the bracket matcher so that the functions `<` and `>` actually work.
* Removed tabs on automatic formatting to avoid problems with different tab widths

And a new feature: Undo/Redo. Now any text field, specifically the REPL and the code editor have an undo/redo stack as they should have had all along. It just uses the <a title="Java Swing: Undo/Redo API" href="http://docs.oracle.com/javase/1.4.2/docs/api/javax/swing/undo/package-summary.html">Swing Undo/Redo API</a>, so it wasn't terribly hard to implement, but it was something that needed to be done. Hopefully this makes it easier on students that accidently delete things (this may have happened, ergo the new feature :-\).
New version is <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">r178</a>.