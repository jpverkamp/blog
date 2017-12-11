---
title: Racket Roguelike - Going on hiatus
date: 2013-05-24 14:00:54
programming/languages:
- Racket
programming/sources:
- 7DRL
programming/topics:
- Games
- Roguelikes
---
It's hard to believe that it's already been almost two months since I first started this series. In that time, it's grown and changed rather a lot.

<!--more-->

The very [first week]({{< ref "2013-04-04-racket-roguelike-1-a-gui-screens-i-o-and-you.md" >}}), all we had was a single `@` moving about on the screen:

{{< figure src="/embeds/2013/runaway.png" >}}

[A week later]({{< ref "2013-04-11-racket-roguelike-2-infinite-caves.md" >}}) and we already have caves, with nice pools and underground trees (that's never really made that much sense, has it?):

{{< figure src="/embeds/2013/water-and-trees.png" >}}

In [week 3]({{< ref "2013-04-18-racket-roguelike-3-rats-rats-everywhere.md" >}}), the caves get quite a bit more dangerous with the introduction of rats, rats, everywhere:

{{< figure src="/embeds/2013/3-attack.png" >}}

Unfortunately (or perhaps not), a rat without an AI isn't much of a threat at all. So [after that]({{< ref "2013-04-25-racket-roguelike-4-slightly-smarter-critters.md" >}}), we started work on making the enemies a bit starter and added a few more dangerous sorts:

{{< figure src="/embeds/2013/7-incoming.png" >}}

In [week 5]({{< ref "2013-05-02-racket-roguelike-5-armors-and-weapons-and-potions-oh-my.md" >}}), we shifted gears to get into gear, adding weapons, armors, and potions (oh my!):

{{< figure src="/embeds/2013/ooh-shiny.png" >}}

Then in [week 6]({{< ref "2013-05-10-racket-roguelike-6-dig-deeper.md" >}}), we brave the depths, finally getting away from those infinite caves and starting out on the surface. Granted, we went right back down, but still. Onward and downward!

{{< figure src="/embeds/2013/2-going-down.png" >}}

Finally, [last week]({{< ref "2013-05-17-racket-roguelike-7-into-darkness.md" >}}) we managed to rid our player of that pesky x-ray vision:

{{< figure src="/embeds/2013/no-more-xray-vision.png" >}}

It's been a long strange road already, but where does that leave us now?

Well, there are a few things that I'd definitely like to implement before moving on:

* Ranged weapons
* Animations decoupled from player movement (to allow for arrows, fire, explosions, etc)
* Terrain modification (in particular: burrowing for monsters and/or players)
* More content! (levels, entities, and items; each is just waiting for more definitions)

I've already started on the first two of those. Granted, as a wise man once (may or may not have) said:

> I have not failed 1,000 times. I have successfully discovered 1,000 ways to NOT make a light bulb.

I will figure it out, it's just taking longer than I'd like. Unfortunately[^1], all that's going to have to wait. It turns out I'm getting married in a week[^2]. Believe it or not, that takes up rather a lot of time. After that, I'll be taking a bit of a vacation from the mad, mad world of academia for a couple of weeks. My intention is to avoid the Internet as much as possible. We'll see how that goes.

The takeaway from all of this? This series isn't over. If anything, it's only going to get a lot deeper in the next few posts--sometime in the third week of June. I hope to see you then!

**Edit**: For part 8, click here: [Racket Roguelike 8: A million words!]({{< ref "2013-06-21-racket-roguelike-8-a-million-words.md" >}})

[^1]: Or really not. :smile:
[^2]: It's amazing how something like that can sneak up on you...