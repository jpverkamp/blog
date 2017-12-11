---
title: Sandbox - It's Alive!
date: 2010-02-06 05:05:39
programming/languages:
- .NET
- C#
programming/topics:
- Games
---
So I haven't actually updated the Sandbox project for quite some time (December 9th I believe).  Since then, I've actually torn out the core of the code and rewritten it to actually be a game, rather than another clone of the general Falling Sand games.  Rather than explain in detail what I've done (I'll get to that later), I'll start with screenshots of the new version.

<!--more-->

{{< figure src="/embeds/2010/main-menu-1.png" >}}

Here we have the main menu.  In the background, there is a running game with four sources along the top, two computer players, and four targets along the bottom.  Sources are where particles spawn, each can have a different color of particle.

Players can either draw walls or erase them.  In this case, there is a player creating dark red walls (currently right above the Quit menu item) and a player removing walls (the circle in the bottom left).  The targets at the bottom keep track of the number of particles that hit them.

You can also see the effects of the wind option in this screenshot.  Currently there is a light wind blowing from right to left.  In the main screen, the wind will vary back and forth.

{{< figure src="/embeds/2010/main-menu-2.png" >}}

Here we have the same main menu, a bit further into a demo game.  As you can see, the targets are starting to collect particles.  Between the "Wind: Yes" and "Play!" options you can see the effect of the erasing player.  It has managed to knock a few holes in the walls for particles to get through.

{{< figure src="/embeds/2010/main-menu-3.png" >}}

To navigate the menu, use the arrow keys on your keyboard (no mouse support just yet).  Up and down will move between menu options while left and right will cycle through the possible values for menu options that have them (currently the top three).  Once you've chosen all of the options that you would like, choose "Play!".

{{< figure src="/embeds/2010/game-1.png" >}}

Here we have a game in progress with 3 players, no AI players, and no wind.  The players are red, green, and blue, in that order.  Each of the players has the same options as the computer players in the title screen: they can either draw walls or erase them.  Each has a target along the bottom of the screen although there is currently no win condition.

See the end of the post for the current controls for each of the players.

{{< figure src="/embeds/2010/game-2.png" >}}

If you push Escape while playing a game, the game will pause and ask if you'd rather keep playing or return to the title screen.

{{< figure src="/embeds/2010/main-menu-3.png" >}}{{< figure src="/embeds/2010/game-3.png" >}}

Here we have a much more complex looking example with a single human player (red), two AI players (the greenish shades), and wind enabled.  As you can see in the bottom center, only the AI player has a target.  Even without complex AI, the AI players are rather good at messing up your plans just by virtue of how quickly they can move (they move just as quickly as you, but never stop).  In a future version, I will probably add in code to add some variance to their speeds.

Anyways, that's the new version.  Check it out!

**Menu Controls:**

* Up/Down - Move through menu options
* Left/Right - Choose possibilities on the current menu option
* Enter - Select the current menu option

**Player Controls:**

* Player 1: Arrow keys, right shift / control to toggle mode
* Player 2: WASD, left shift / control to toggle mode
* Player 3: IJKL, P / ; to toggle mode
* Player 4: Numpad 8462; Numpad minus / plus to toggle mode
* Escape to pause / bring up menu

**Downloads:**

* **{{< figure link="Sandbox-0.2.34.zip" src="/embeds/2010/Sandbox 0.2.34" >}}**
* **{{< figure link="Sandbox-0.2.34-Source.zip" src="/embeds/2010/Sandbox 0.2.34 (Source)" >}}**
* If you may not have .NET 3.5: **[click here](http://www.asoft.be/downloads/netver2007.zip)**
* To install SDL.NET: **[click here](http://sourceforge.net/projects/cs-sdl/files/)**

Note: I've update the version numbers to 0.2.* to represent the complete rewrite of the game's core.  The * will represent the current revision number that I'm working with so will always increase and may skip several values between releases.

Note: The download has increased somewhat in size because some of the graphics / game fonts used are embedded in the executable.  If this becomes a problem, let me know and I'll see what I can do.  It's still only a 42 KB, so I doubt this will be a problem. (The images in this page are larger).