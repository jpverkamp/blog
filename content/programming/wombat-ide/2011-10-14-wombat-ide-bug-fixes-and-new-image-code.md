---
title: Wombat IDE - Bug fixes and new image code
date: 2011-10-14 04:55:36
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
First, bug fixes:

* Fixed an issue that made the C211 libraries disappear on a reset
* `list` should be printed as a procedure (rather than a type)
* Fixed a problem where reload would fail
* Fixed a problem where the wrong procedure name would be printed in errors in make-image and image-map
* Added code to automatically add a git tag on deploy (based on the version number)

Also, I've rewritten the image code (especially `read-`, `write-`, and `draw-image`) to make them significantly faster. They were already faster then the pure Scheme versions, but this should add at least a bit more. It will be particularly helpful later in the semester during some of the more image heavy assignments.

Edit: The most up to date C211 image library API can be found <a title="C211 Image API" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-image.htm">here</a>.