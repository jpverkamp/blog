---
title: Sandbox - Multiple definitions
date: 2009-12-09 06:45:34
programming/languages:
- .NET
- C#
programming/topics:
- Games
---
Added a few new features that I've been hoping to add for a bit now.

**Screenshots:**

{{< figure src="/embeds/2009/Sandbox-0.1.6-Complex-wall-structure.png" >}}

<!--more-->

First, we have a more complex wall structure.  I actually grew the walls in the center using Red Crystals in the Crystal definition file.  (See the new features).

Another (definition) feature is the addition of soil.  Soil is a solid that, when watered, will grow plants.  So now the plants will keep coming back every time you burn them to the ground.  Great fun!

{{< figure src="/embeds/2009/Sandbox-0.1.6-Burn-it-all-down.png" >}}

Of course I had to light everything on fire at least once... I like how the fire is running through the maze of walls that I've placed.

{{< figure src="/embeds/2009/Sandbox-0.1.6-Growing-red-crystals.png" >}}

Here's a sneak peak at the Crystals definition.  The Red Crystals grow more or less like a circuit board, spreading out.  The Green Crystals grown in much more solid blocks.  The Blue Crystals?  You'll just have to try it and find out.  Remember, PgUp and PgDown will switch between definition files.

**New features:**

* Use PgUp and PgDown to switch between definition files
* Added Crystals definition file to grow different kinds of crystals
* Expanded definition syntax (not backwards compatible, sorry)
* Minimum and maximum concentrations possible

**Downloads:**

* **{{< figure link="Sandbox-0.1.6.zip" src="/embeds/2009/Sandbox 0.1.6" >}} **
* **{{< figure link="Sandbox-0.1.6-Source.zip" src="/embeds/2009/Sandbox 0.1.6 (Source)" >}} **
* If you may not have .NET 3.5: **[click here](http://www.asoft.be/downloads/netver2007.zip)**
* To install SDL.NET: **[click here](http://sourceforge.net/projects/cs-sdl/files/)**

**Controls:**

* Esc/Q – Quit the program
* B – Toggle border behavior
* P – Pause / Unpause
* Space – Advance the simulation one step (when paused)
* Left-click – Add a blob of the current kind of particle
* Right-click – Remove a blob of any kind of particle
* 1-9 – Select the corresponding kind of particle
* PgUp - Load the previous definition file (alphabetically)
* PgDown - Load the next definition (alphabetically)
