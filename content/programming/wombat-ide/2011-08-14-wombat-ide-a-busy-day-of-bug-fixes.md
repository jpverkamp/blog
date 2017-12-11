---
title: Wombat IDE - A busy day of bug fixes
date: 2011-08-14 05:05:38
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: a-busy-day-of-bug-fixes
---
Today was a busy day of bug fixes, mostly minor. Here's a nice list:

* Added building the [webstart](http://www.oracle.com/technetwork/java/javase/tech/index-jsp-136112.html "Java Webstart Technology") files to the automatic build system
* Removed references to the old [SISC](http://sisc-scheme.org/ "Second Interpreter of Scheme Code") code
* Fixed a crash when the syntax definitions couldn't be loaded successfully
* Fixed an error with dynamically reloading options
* Added better sanity checks to option loading, defaulting to known values if necessary

All of this has prompted a new build: r113, available <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>.