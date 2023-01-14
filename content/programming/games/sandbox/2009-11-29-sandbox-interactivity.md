---
title: Sandbox - Interactivity
date: 2009-11-29 02:10:14
programming/languages:
- .NET
- C#
programming/topics:
- Games
- Falling Sand
---
I know I've already updated this project twice within the past 24 hours, but third time's a charm.  This time, it's interactive!

I'm using the same rules as last time (with the tweaks I mentioned).  The main difference are that you can left-click anywhere on the screen to add a blob of fire or right-click to add a new blob of plant.  It's still not really a game per-say, but it's got the makings of one!

<!--more-->

**Screenshots:**

{{< figure src="/embeds/2009/Sandbox-0.1.3-Pre-plant.png" >}}

The default state of the current version--the screen will fill with water raining down.

{{< figure src="/embeds/2009/Sandbox-0.1.3-Growing-fast.png" >}}

Aww.  They grow up so fast... Sprouting like weeds as it were... Ok, I'm done.  Anyways, the plants are growing rather well.

{{< figure src="/embeds/2009/Sandbox-0.1.3-A-beginning-on-fire.png" >}}

With a single click, a fire starts... Remember kids, you and only you can prevent forest fires!

{{< figure src="/embeds/2009/Sandbox-0.1.3-Almost-completely-gone.png" >}}

The fire eats away quickly at the plant and--for now--pretty evenly.  It would just be a matter of tweaking the definitions to get the fire to burn a little less evenly.  The gray stuff that's following the first is smoke.  The yellow at the head of the fire is the newly burnt plants (known in the definitions as Spark).

{{< figure src="/embeds/2009/Sandbox-0.1.3-Aftermath.png" >}}

After the fire burns itself out, the simulation basically resets to the falling water.  Here, you can see the large dent that the fire left in the center of the water stream.

**Downloads:**

* **{{< figure link="Sandbox-0.1.3.zip" src="/embeds/2009/Sandbox 0.1.3" >}}**
* **{{< figure link="Sandbox-0.1.3-Source.zip" src="/embeds/2009/Sandbox 0.1.3 (Source)" >}}**
* If you don't know if you have .NET 3.5: **[click here](http://www.asoft.be/downloads/netver2007.zip)**
* To install SDL.NET: **[click here](http://sourceforge.net/projects/cs-sdl/files/) **

**Controls:**

* Esc/Q – Quit the program
* F1 – Toggle region display mode
* B – Toggle border behavior
* P – Pause / Unpause
* Space – Advance the simulation one step (when paused)
* Left-click - Add a blob of fire
* Right-click - Add a plant blob
