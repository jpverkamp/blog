---
title: Wombat IDE - Bug fixes
date: 2011-09-15 04:55:35
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
A small list of bug fixes:

* Fixed printing for empty strings and Kawa specific strings (derived from gnu.lists.FString)
* Fixed a problem with the Ant script when the build directory didn't previously exist
* Fixed random to correctly deal with large numbers (larger than the range of a Java `int`)

The new build is <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">r194</a>.