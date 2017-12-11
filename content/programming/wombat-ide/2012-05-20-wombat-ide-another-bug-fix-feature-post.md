---
title: Wombat IDE - Another bug fix / feature post
date: 2012-05-20 04:55:12
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
Additional features:

* Since both the image and turtle libraries need the same color code, I've factored that out into it's own module: `[(c211 color)](http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-color.htm "C211 Color API")`
* [Issue 193](https://code.google.com/p/wombat-ide/issues/detail?id=193 "Issue 193"): Opening a file on top of an empty  replaces that document.

Bug fixes:

* Fixed documentation issues with image->list, list->image,
* [Issue 187](https://code.google.com/p/wombat-ide/issues/detail?id=187 "Issue 187"): Fixed the direction parameter to `hatch` to take degrees rather than radians to match the rest of the library.
* Made links in the about dialog clickable.
* [Issue 186](https://code.google.com/p/wombat-ide/issues/detail?id=186 "Issue 186"): Fixed the recent document manager on documents with the same name.


<!--more-->

Also, we now have a launcher image:

{{< figure src="/embeds/2012/loading.png" >}}

(<a title="Wombat Image Source" href="http://www.nongnu.org/neurowombat/resources.html">Source</a>, <a title="Creative Commons Public License" href="https://creativecommons.org/licenses/by-sa/1.0/legalcode">License</a>)

Finally, there's been one change to the <a title="C211 Image API" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-image.htm">Image API</a>:

* The generating function to `make-image` now takes only two arguments, `row` and `column`. The `rows` and `columns` arguments have been dropped. The change is reflected in the [online API](http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-image.htm "C211 Image API").
