---
title: Wombat IDE - A pile of minor changes
date: 2011-11-24 04:55:03
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
I've been putting off a new release for a while while I collect a number of minor bug fixes and enhancements, but I think it's about time to actually release them. <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">1.327.1</a> is the new build.

<!--more-->

A few bug fixes:

* Fixed a bug on some *nix machines where the launcher wouldn't find the correct directory (the directory is now derived from the running JAR's location)
* Fixed a type typo in `image-ref`
* Added a corrected error message for negative array indexes (for example, trying to make an image with a negative size)
* Added a bunch of mapped types to error messages (numbers, voids, strings, etc)

And a few new features:

* Added a link to the launcher to the index page
* Moved all of the IDE related files into their own directory in preparation to split development (the launcher is a second project at the moment)
* `#void` will print when nested in another structure `(list (void))`, but not directly
* Added the function `atom?`

<span style="font-family: monospace;">
</span>