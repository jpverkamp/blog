---
title: Wombat IDE - Updated syntax, documentation
date: 2012-04-30 04:55:41
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
First, a few bug fixes with the keyword lists and help links:

* Added a bit of code to differentiate between a normal `let` and a named `let`.
* Fixed for losing the syntax definitions on some systems.

Also, I wrote code to generate help files for the C211 libraries. Theoretically, I should just be able to update these with future updates to the APIs:

* [Image API](http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-image.htm "C211 Image API")
* [Matrix API](http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-matrix.htm "C211 Matrix API")
* [Tree API](http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-tree.htm "C211 Tree API")
* [Turtle API](http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-turtle.htm "C211 Turtle API")
* [Color API](http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-color.htm "C211 Color API") (Edit: Added 19 May after re-factoring of colors)

As a side note, I've added two new functions to the tree API:

* `(left-subtree? tr)` - returns `#t` if the given tree has a non-empty left subtree
* `(right-subtree? tr)` - returns `#t` if the given tree has a non-empty right subtree
