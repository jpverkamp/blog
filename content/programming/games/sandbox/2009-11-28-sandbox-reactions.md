---
title: Sandbox - Reactions
date: 2009-11-28 15:30:27
programming/languages:
- .NET
- C#
programming/topics:
- Games
- Falling Sand
---
So I stayed up entirely too late last night / this morning and decided to go ahead and add reacti0ns to Sandbox.  Turns out, it was far easier than anything that I've implemented thus far on this project.  I spent some of the day (when I wasn't at the family Thanksgiving celebration) tweaking a few things to make it look a little better.

Basically, reactions have four parts: a core, reactants, a chance, and (possibly) a product.  The core is the particle that will be reacting.  The reactants (each given with a concentration) are the neighboring particles.  The chance adds a bit of randomness to reactions and allows particles to fade (see the fire below).  The product (if present) is the result of the reaction.

<!--more-->

Overall, it's a pretty simple system with some pretty awesome effects.  Check out the screenshots and downloads towards the end.

**Current progress:**

* Added reactions based on reactants and/or random chance.
* Added definitions for plants (grown when watered) and fire (burn plants).

**Things to do:**

* Allow the user to paint the canvas with different materials.
* Add emitters.

**Screenshots:**

**{{< figure src="/embeds/2009/Sandbox-0.1.2-A-drop-to-drink.png" >}}**

The blue at the top is water falling downwards.  The red in the middle represents a torch (that won't go out even with the water pouring over it).  The green line along the bottom is a plant base.  The basic idea is that the water will fall onto the plants, the plants will grow up to the torch, and the torch will burn the plant back down.

{{< figure src="/embeds/2009/Sandbox-0.1.2-Growing.png" >}}

For how simple the system is, the plants actually look pretty good when they grow.  It's called {{< wikipedia "emergence" >}}and is one of the tenets of {{< wikipedia "swarm intelligence" >}}--one of the parts of {{< wikipedia "artificial intelligence" >}} I am particularly interested in.  In any case, the plants have just about reached the fire.

{{< figure src="/embeds/2009/Sandbox-0.1.2-Spreading-flames.png" >}}

Then the fire reaches the plants!  It's rather spectacular as the plants try to grow up while the fire is burning them down.  I modeled the actual behavior of the fire using two types of particles: fire and sparks.  Fire is modeled as a gas (flowing upwards) and will randomly convert into sparks (falling down) so that it can more easily burn the plants beneath it.

{{< figure src="/embeds/2009/Sandbox-0.1.2-Burnt-out.png" >}}

Due to a bug in how the grid is arranged, the line of plants along the bottom is not actually checking if it should be on fire (it's on the top of an inactive region) so it's not actually burning.  I've already fixed this issue and I'll put it in with the definitions for the next version.  In any case, here you can see the plants growing just fast enough to create a more or less continual fire at the base of the falling water.

**Downloads:**

* {{< figure link="Sandbox-0.1.2.zip" src="/embeds/2009/Sandbox 0.1.2" >}}
* {{< figure link="Sandbox-0.1.2-Source.zip" src="/embeds/2009/Sandbox 0.1.2 (Source)" >}}

**Keyboard shortcuts:**

* Esc/Q – Quit the program
* F1 – Toggle region display mode
* B – Toggle border behavior (does not correctly reactivate particles yet)
* P – Pause / Unpause
* Space – Advance the simulation one step (when paused)
