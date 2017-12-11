---
title: Wombat IDE - Updated tree and image libraries
date: 2012-02-18 04:55:59
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
Continuing the update to the Petite back-end, I've rewritten the [matrix library]({{< ref "2011-12-13-wombat-ide-c211-matrix-library.md" >}}) and most of the[ image library]({{< ref "2011-08-27-wombat-ide-c211-tree-and-image-libraries.md" >}}) (everything except for `read-image`, `write-image`, and `draw-image`). The current code is all in Scheme, although I don't want to write the image loading/saving code in Scheme otherwise we'll be back into the original situation with the C211 libraries. The APIs haven't changed though, so the previous APIs are still valid:

<!--more-->


* [C211 Matrix API]({{< ref "2011-12-13-wombat-ide-c211-matrix-library.md" >}}) (Edit: Most up to date version [here](http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-matrix.htm "C211 Matrix API"))
* [C211 Image API]({{< ref "2011-08-27-wombat-ide-c211-tree-and-image-libraries.md" >}}) (Edit: Most up to date version [here](http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-image.htm "C211 Image API"))

The only difference is that the libraries are no longer loaded by default. To load the libraries, you need to import them:

```scheme
(import (c211 matrix))
(import (c211 image))
```

If you want to switch over to the new versions of Wombat, you can get it <a title="Wombat Launcher Download" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>. You should have at least version 2.48.12.