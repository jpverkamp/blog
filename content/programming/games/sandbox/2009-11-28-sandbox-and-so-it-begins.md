---
title: Sandbox - And so it begins
date: 2009-11-28 06:45:52
programming/languages:
- .NET
- C#
programming/topics:
- Games
---
For the past few years, I've been fascinated by falling sand / particle simulation type games (<a href="http://fallingsandgame.com/sand/">like this one</a>).  Enough so that I've set out to make one a fair number of times.  Each time, I've advanced my own techniques by a little bit, finding new and better ways to make digital sand.

This time around, I'm going to try to use C# with <a href="http://cs-sdl.sourceforge.net/index.php/Main_Page">SDL.NET</a> for all of my graphical work and a simple grid for all of the particle data.  Rather than looping over the grid, I will be using {{< wikipedia page="Quadtree" text="quadtrees" >}} to only update the regions that actually need to be updated.  So far the results are promising!

<!--more-->

The last implementation of Sandbox (using C# and <a href="http://www.agatelib.org/">AgateLib</a>) that I tried used a list of particles and could handle about 20,000 particles before slowing down

Check out below for screen shots and downloads from the first version.  The executable should run if you have <a href="http://www.microsoft.com/downloads/details.aspx?FamilyId=333325FD-AE52-4E35-B531-508D977D32A6&amp;displaylang=en">.NET 3.5</a> (which you should either have already or only have to download once) and <a href="http://sourceforge.net/projects/cs-sdl/files/">SDL.NET</a>.  Theoretically, it should also work perfectly well with Mono, although I haven't had a chance to try it yet.  When I get back to campus and can test it on a Linux machine, I'll let you know.

**Current progress:**

* Particles work.
* Three kinds of matter - solids (don't move), liquids (fall down), and gasses (drift up)
* Static walls and emitters for now

**Things to do:**

* Add reactions so that particles interact besides just hitting each other.
* Add actual emitters (possibly as a reaction).
* Add dynamically placed walls and/or emitters.

**Screenshots:**

{{< figure src="/embeds/2009/Sandbox-0.1.1-Starting-out.png" >}}

First, the simulation just starting out.  It's been a second or two and we already have over 2,000 particles on the screen.

{{< figure src="/embeds/2009/Sandbox-0.1.1-Piles-of-sand.png" >}}

After a little longer, the sand has really started to pile up.  Now we have 10 times as many particles.  Believe me, the system can handle far more than that.

{{< figure src="/embeds/2009/Sandbox-0.1.1-Display-regions.png" >}}

This shot shows the same number of particles as before with the alternate display mode.  Here we can see the regions that are currently active (in red) and the region that do not need to be updated (in blue).  One thing to note is that once particles settle down (in the middle for example), they don't need to be updated until something happens.

Currently, the quadtrees are set to use OR as their boolean logic base.  That means that if one subregion is active, the overall region is active.  What this means from a simulation standpoint is that inactive regions are grouped but active regions are not (for now).  It seems counter-intuitive to me, but this is actually faster than using an AND tree.  I hope to add the ability to switch between the two in the future.

{{< figure src="/embeds/2009/Sandbox-0.1.1-Lots-of-sand.png" >}}

Here the simulation has been running for a minute or two.  There are currently 85,000 particles on the screen.  I was originally going to show another factor of 10 increase, but the particles were falling off of the screen fast enough to make that impractical.  One interesting thing to note is the extended edges on each side of the center.  The particles are falling against each other with the liquid (falling) particles pushing against the gas (rising) particles, forming an additional wall.  Something of an emergent behavior... very shiny!

{{< figure src="/embeds/2009/Sandbox-0.1.1-Complex-regions.png" >}}

The same time in the simulation as the previous image, showing the display regions.  There are quite a few more divisions that earlier but the ability to not draw regions that are not updating is still quite a time saver.

**Downloads:**

* **{{< figure link="Sandbox-0.1.1.zip" src="/embeds/2009/Sandbox 0.1.1" >}}**
* **{{< figure link="Sandbox-0.1.1-Source.zip" src="/embeds/2009/Sandbox 0.1.1 (Source)" >}}**

**Keyboard shortcuts:**

* Esc/Q - Quit the program
* F1 - Toggle region display mode
* B - Toggle border behavior (does not correctly reactivate particles yet)
* P - Pause / Unpause
* Space - Advance the simulation one step (when paused)

- Updated matter definition file to use attributes instead of nested elements.
- Moved global variables into main program file.
- Fixed bug (< vs <=) in quadtrees.
- Updated region display mode to display active regions in red, inactive in blue.
- Fixed stuck particle bug.
