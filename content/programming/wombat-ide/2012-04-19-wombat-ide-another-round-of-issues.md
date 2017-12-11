---
title: Wombat IDE - Another round of issues
date: 2012-04-19 04:55:37
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
I have a new chunk of issues this time, this time with screen shots.
### Updated turtle library with new names
Essentially, I've changed a few of the names in the [previous turtle API]({{< ref "2012-04-13-wombat-ide-turtle-graphics.md" >}}) and added a few new alias.

* `spawn` has been renamed to `hatch`
* `split` has been been renamed to `clone`
* `teleport!` has been added as an alias to `move-to!`
* `turn-counter-clockwise!` has been added as an alias to `turn-left!`
* `turn-clockwise!` and `turn!` have been added as aliases to `turn-right!`


<!--more-->

### Fixed <a title="Issue 176" href="http://code.google.com/p/wombat-ide/issues/detail?id=176">issue 176</a>: flush buffer on newlines so it can play nicely with live-display
Previously, output from Petite was being buffered until whatever command was running finished; however, this had problems with things like `live-display`. If you wanted to print something out every frame of an animation (a progress indicator for example), then it would only print at the end. With the new [event driven code]({{< ref "2012-04-11-wombat-ide-a-new-way.md" >}}), it's possible to print after every newline.
### Fixed <a title="Issue 172" href="http://code.google.com/p/wombat-ide/issues/detail?id=172">issue 172</a>: add a red border to the REPL when running long running code.
There have been times when I wanted to be able to quickly tell if code was still running or if it had already finished. Technically, the Run and Stop buttons on the toolbar will tell you that, with the Run button only active if Petite is ready for a command and the Stop button only active if Petite is currently running:

{{< figure src="/embeds/2012/run-stop.png" >}}

However, since this is easy enough to miss, I've added an indicator to the REPL itself that will tell you when the program is running. On short running programs, you'll barely even notice it, but on longer ones, the border of the REPL will turn red when no further commands can be run:

{{< figure src="/embeds/2012/red-ring.png" >}}

Side note: that bit of code that's currently running is called omega. It's one of the shortest infinite loops to write--technically `(let x () (x))` is shorter--and thus useful for testing things like this. So useful in fact, that you can technically just type in `(omega)` to run it. Not that I suggest doing that in your day to day programming. :smile:
### Fix for <a title="Issue 168" href="http://code.google.com/p/wombat-ide/issues/detail?id=168">issue 168</a>, prevent manual resizing of the image window.
At some point, I updated the `draw-image` window with a few new features:

{{< figure src="/embeds/2012/new-draw-image1.png" >}}

Basically, the three buttons along the top are new. You can either zoom out or in using the `-` and `+` buttons or you can directly save the image being displayed (at the current zoom level) without having to go back into Scheme and save it. This window is also used for `draw-turtle` and the turtle `live-display` code, so you can zoom in on turtles the same as on images. The bug fix was to prevent the window from being resized (since the zoom will automatically resize it). While I was at it, the mouse will now follow the zoom button allowing you to click more than once to zoom in/out farther without losing the button.
### Fixed <a title="Issue 146" href="http://code.google.com/p/wombat-ide/issues/detail?id=146">issue 146</a>: progress bar on formatting.
Automatic formatting of code on F6 has been a part of the program pretty much since the beginning, but one feature that I just now added was a progress bar to show you how much longer it will take to format your code:

{{< figure src="/embeds/2012/format-progress.png" >}}
### 
