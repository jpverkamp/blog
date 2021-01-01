---
title: Board Game Cup
date: 2020-12-30
---
I play ... a lot of board games. This year has been hard to do that in person[^tactile], but I still get a chance from time to time. Most recently, I played [Century: A New World](https://boardgamegeek.com/boardgame/270970/century-new-world).[^bgreviews]

One component I really love that came with that game was a set of four small plastic bowls that hold the various goods (colored wooden cubes). It's... kind of brilliant. There are a few other games that could use something like that (*cough cough* [Lords of Waterdeep](https://boardgamegeek.com/boardgame/110327/lords-waterdeep))... and I have a 3D printer. Let's make some!

{{< figure src="/embeds/maker/board-game-cup/final-cup.jpg" >}}

Links:

* [FreeCAD file](/embeds/maker/board-game-cup/board-game-cup.FCStd)
* [Small cup STL](/embeds/maker/board-game-cup/board-game-cup-small.stl)
* [Larger cup (pictured above) STL](/embeds/maker/board-game-cup/board-game-cup-small.stl)

<!--more-->

In my ever going quest to make only a design or two with each CAD program, this time I'm actually trying out [FreeCAD](https://www.freecadweb.org/). It actually seems to work most similiarly to what I used to use years ago, where you create a sketch and then put constraints on it, so getting back into it was a breeze. And it doesn't save via the Cloud[^seriously]. So that's a plus. 

It's actually a pretty easy design too:

{{< figure src="/embeds/maker/board-game-cup/sketch.png" >}}

A 1mm thick surface (using `equals` constraints to make sure they're all the same if I change any one of them), a small indentation so it's not resting completely flat on the table, and a pair of arcs centered on the same point. The three main dimensions (`15mm`, `30mm`, and `35mm` in the sketch above) are all editable and you can make many sizes. That's how I ended up with the [small cup](/embeds/maker/board-game-cup/board-game-cup-small.stl) first, when I accidently miswrote the sizes and the [larger cup](/embeds/maker/board-game-cup/board-game-cup-small.stl) that I actually am using. 

It's fun to print these too. You do want supports (although it might work without them), but they're minimal and the cup pops right off. I like the result, it looks cool:

{{< figure src="/embeds/maker/board-game-cup/final-cup-supports.jpg" >}}

I should probably clean that. 

Now a day of printing later and I have four of them! Woot. Lords of Waterdeep, here we come!

[^tactile]: There's just something about the tactile sensation that online solutions like [Tabletopia](https://tabletopia.com/) and BoardGameArena(https://boardgamearena.com/) miss out on.

[^bgreviews]: I should review games too. As likely to be read as anything else I do and I like looking back. :)

[^seriously]: Seriously Fusion 360, what's up with that? 