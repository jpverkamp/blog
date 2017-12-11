---
title: Wombat IDE - A problem with characters
date: 2011-12-07 04:55:17
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
Previously character literals (of the form `#\a`, `#\space`, etc) were messing with automatic indentation and bracket matching (mostly, if you tried to do `#\(` or `#\)` ), but now it's fixed.

Update to version <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">1.340.13</a> if this has been a problem.