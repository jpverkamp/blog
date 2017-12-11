---
title: Wombat IDE - Minor bug fixes
date: 2011-10-17 04:55:51
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
Just a few bug fixes this time:

* A few fixes for error message related to incorrect usage of car and cdr to better match what Chez gives
* Tweaks to clean up the build system
* Fixed the JAR signing system to automatically sign JARs only if they're out of date (prevents Webstart from re-downloading them)
