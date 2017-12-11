---
title: Wombat IDE - Images are annoying sometimes
date: 2011-11-26 04:55:49
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
There have been two image bugs that have been bothering me for a while.

* Occasionally error messages will crop up showing an `IndexOutOfBoundsException`. I've fixed most of those, but I finally found a new one dealing with strange negative array indices.
* Some images don't work correctly with `read-image`. I haven't been able to determine why (I should be able to deal with any image that Java's JAI can read), but I finally tracked it down to some kinds of grayscale images. I was assume that they'd be of the type `ARGB` rather than converting. Fixed now.

All together, the image library should be a bit more stable now in the newest build: <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">1.329.19</a>.