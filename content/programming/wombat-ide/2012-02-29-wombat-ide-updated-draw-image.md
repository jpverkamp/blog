---
title: Wombat IDE - Updated draw-image
date: 2012-02-29 04:55:40
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
After a long while, I've actually done some work on the frame displayed with `draw-image`. Now rather than just showing the basic image, there's a bit of extra information available.

<!--more-->

{{< figure src="/embeds/2012/new-draw-image.png" >}}

The new dialog will show the size of the image, the current size it is being drawn at (which will automatically scale with the size of the dialog), and the color being displayed under the cursor. In addition, the initial size of the dialog is based on the size of the image, automatically scaling images that would normally be either too small or too large to sensibly display.

As a small side note, the predefined colors from the [old image API]({{< ref "2011-08-27-wombat-ide-c211-tree-and-image-libraries.md" >}}) are now defined again.

Edit: The newest C211 Image API can be found <a title="C211 Image API" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-image.htm">here</a>.

If you would like to download the new version of Wombat, you get get the launcher <a title="Wombat Launcher Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>. You should have at least version 2.58.2.