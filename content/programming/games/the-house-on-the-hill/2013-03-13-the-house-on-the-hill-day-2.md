---
title: "The House on the Hill \u2013 Day 2"
date: 2013-03-13 14:00:02
programming/languages:
- Racket
- Scheme
programming/sources:
- One Game a Month
programming/topics:
- Games
- Roguelikes
---
The problem with starting with a (far) less common language is that you have to develop your own tools. That's what I ended up spending most of the day doing in the case of Racket, although I think it ended up being a rather worthwhile endeavor.

<!--more-->

The basic API is based on <a title="Rot.js on GitHub" href="http://ondras.github.com/rot.js/">Rot.js</a> ((And I'm sure a dozen other libraries besides)) and has the following functions:

* `create-gui title tiles-wide tiles-high [tile-size 12] [key-listener #f]` - create a new GUI
* `clear`
  * `clear gui` - clear the entire screen in black
  * `clear gui bg` - clear the entire screen in a given color
  * `clear gui x y width height` - clear a section with black
  * `clear gui x y width height bg` - clear a section with a given color
* `flip gui` - flip the double buffer (has to be done manually)
* `draw-tile gui x y tile [fg "white"] [bg "black"]` - draw a single character tile (any unicode character)
* `draw-string gui x y str [fg "white"] [bg "black"]` - draw a string starting at the given x, y
* `draw-centered-string gui y str [fg "white"] [bg "black"]` - draw a screen centered on the given row

I'll probably add a few more methods and possibly even put it <a title="Racket: PLaneT" href="http://planet.racket-lang.org/">PLaneT</a> (a central repository for Racket libraries), but all that will have to wait until after 7DRL is done. At the moment, I just don't have time.

That being said: With the GUI in place, now I have time for screenshots! Here are a few quick snapshots of my progress (click to embiggenate, theoretically):

{{< figure src="/embeds/2013/1-first-working-gui.png" >}}

To start out with (and get the font and layout correct), I just filled the screen with numbers. This also let me know when I finally managed to set the size of the `canvas%` inside of the `frame%` rather than the `frame%` itself. In the original case, I was cutting off a few rows due to the height of the title bar. Oops!

{{< figure src="/embeds/2013/2-with-title.png" >}}

Next, I wanted to make sure that `draw-centered-string` was working (which implies that `draw-string` is working since the one relies on the other). This also showcases using the `clear` command as well--that's what I used to clear the area around the text. You may also notices a few seemingly random characters all over the place. This is from experiments in multi-threading. It worked great! I love Racket's threads.

{{< figure src="/embeds/2013/3-variable-font-size.png" >}}

Here's an example of a different font size. I made sure that you specify the GUI size by tile size, number of tiles wide, and number of tiles high. That should keep it nicely pixel-size-independent. For whatever that is worth. :smile:

{{< figure src="/embeds/2013/4-keyboard-events.png" >}}

Here's an example of keyboard input working. This actually went really quickly once I figured out that I had to subclass `canvas%` to get it to work. I'm still not really familiar with the object oriented parts of Racket (my own code for this project is a weird mix of functional and non-OO procedural code), but I'm getting there.

{{< figure src="/embeds/2013/5-title-screen.png" >}}

Finally, we have the real title screen. Woo for real progress!

{{< figure src="/embeds/2013/6-starting-the-game.png" >}}

And finally, here is the simulated start screen. It doesn't actually do anything (not even move around yet) but I have all of the drawing code out of the way. I should be able to hammer out movement and room rendering tomorrow. That will leave more room definitions, items, monsters, and events for Thursday and just content adding / debugging for Friday. Believe it or not, I'm still completely confident that I can do it. Perhaps I'm just crazy like that. :smile:
