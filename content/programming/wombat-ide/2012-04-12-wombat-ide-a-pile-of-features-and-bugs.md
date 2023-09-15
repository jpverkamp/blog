---
title: Wombat IDE - A pile of features and bugs
date: 2012-04-12 04:55:09
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
Another one of those posts. :smile:

Bug fixes:

* Fixed a problem with the interop libraries reporting they were finished before they actually were. Now when reading a few hundred images, the call will block until they are actually read rather than just pretending to read them as it was.
* [Issue 158](http://code.google.com/p/wombat-ide/issues/detail?id=158 "Issue 158"): Prevent backups of backup files (no double ~). Basically, if a person directly edits a backup file, they're on their own.
* [Issue 163](http://code.google.com/p/wombat-ide/issues/detail?id=163 "Issue 163"): Better image scaling for the `draw-image` dialog.
* Fixed a few minor copy/paste errors in the [matrix library]({{< ref "2011-12-13-wombat-ide-c211-matrix-library.md" >}}).
* The dialog produced by `draw-tree` now has the same background color as that produced by `draw-image` or `draw-matrix`.

Enhancements:

* [Issue 160](http://code.google.com/p/wombat-ide/issues/detail?id=160 "Issue 160"): The relative paths for `read-image` and `write-image` now respect the path set by the current-directory function rather than the relative path set by Java.
* [Issue 162](http://code.google.com/p/wombat-ide/issues/detail?id=162 "Issue 162"): Added a menu option to load files directly into the REPL without opening them. This should be useful for things like large datafiles (still written in Scheme though).
* Added initial version of a [[wiki:turtle graphics]]() library. I'll talk about this more when I finish it.

The Wombat launcher will automatically download the newest version for you. If you don't have the launcher, you can get it <a title="Wombat Launcher Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>.
