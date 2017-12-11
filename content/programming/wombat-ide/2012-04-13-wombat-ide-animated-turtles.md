---
title: Wombat IDE - Animated turtles
date: 2012-04-13 18:01:58
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
Sometimes I keep going beyond the point where I probably should. In this case, I want to add an animation feature to the turtle graphics library so I just went ahead and wrote one.

These new functions have been added to the turtle API:

* `(live-display b)` - `b` should be `#t` or `#f` to enable or disable the live display, default is `#f`
* `(live-delay n)` - set the timer between frames, default is 0.1 seconds
* `(live-display)` - is live display enabled?
* `(live-delay)` - get the current delay


<!--more-->

Here's an example of the [same star]({{< ref "2012-04-13-wombat-ide-turtle-graphics.md" >}}) from the previous post:

{{< figure src="/embeds/2012/star.gif" >}}

Side note: There's not actually a way to save an image like this directly. I added in code to write out each turtle using `(write-image (turtle->image t))` for each frame and then combined them using the <a title="GIMP - The GNU Image Manipulation Program" href="http://www.gimp.org">the GIMP</a>. Hopefully I can actually add that directly to the program before too long.

Edit: The most updated Turtle API can be found <a title="C211 Turtle API" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-turtle.htm">here</a>.