---
title: The House on the Hill - Day 4
date: 2013-03-15 14:00:52
programming/languages:
- Racket
- Scheme
programming/sources:
- One Game a Month
programming/topics:
- Games
- Roguelikes
---
Today was fairly productive, although even with that I managed to fall a bit behind. So it goes.

<!--more-->

The first thing that I did today was to rewrite the drawing code so that it loops across the rooms rather than the tiles ([as I mentioned yesterday]({{< ref "2013-03-14-the-house-on-the-hill-day-3.md" >}})). The code is not only far more efficient, it actually wasn't as complicated as I feared. It also lets me draw the walls between rooms only on rooms that have already been generated. Here's a screen shots of that in action:

{{< figure src="/embeds/2013/3-a-few-more.png" >}}

This also shows a few of the new rooms that I've defined. The two in the top are ballrooms (that's supposed to be a piano in the top right...) and the one on the right is a garden with a stone table. In addition to those, we now have definitions for a coal chute, a dining room, and a graveyard.

Another thing that I did was actually hook up the code for the player. Now that code I showed back on [Day 1]({{< ref "2013-03-12-the-house-on-the-hill-day-1.md" >}}) with the *on-walk* events actually works. Granted, I've changed the syntax from Racket's {{< doc racket "keyword arguments" >}} to their {{< doc racket "object oriented model" >}}, but it's the same idea. To see what it would look like now, here's the chasm definition:

```scheme
(define-room
  [name "chasm"]
  [floors '(basement)]
  [doors '(west east)]
  [floorplan
   '("         "
     "         "
     "         "
     "||| |||||"
     "|||||| ||"
     "|||||||||"
     "         "
     "         "
     "         ")]
  [tiles
   (list 
    (define-tile
      [tile " "]
      [name "empty space"]
      [description "a seemingly endless drop into darkness"]
      [on-walk
       (lambda (player tile)
         (when (send player ask "Are you sure you want to step into the empty space?")
           (send player die "You fall screaming into the abyss.")))])
   ...)])
```

I think the syntax is a lot cleaner and more Racket-like. I am wrapping the call to `(new room% ...)` with a macro that rewrites it to `define-room`, but that's it. 

So at this point, we actually have a mostly playable game. You can wonder around the house for quite a while and there are several ways to lose the game (you'll either have to play it or read the source code to find out how :smile: ). Granted, there are no events and no ways to win, but I'm getting there! I may actually have some time this weekend to work, so all is not lost.

Here are a few more screenshots:

{{< figure src="/embeds/2013/4-error-tiles.png" >}}

Here's what happens if you forget to define a tile in a room definition. Rather than freezing up the game (as it was doing a little while ago), now it will display a pink § character. If you so happen to be using that as one of the characters in the game... oops? I do need to figure out how to fix the tiles that are extending beyond the bottom of a given square. It's common enough that it's becoming annoying. Most likely, all that it will need is a different font.

And yes, this is the same as the original board game. You can build a nice circular house that completely encloses the entrance. It's non-trivial but entirely doable.

{{< figure src="/embeds/2013/6-oops.png" >}}

And here's what happens if you manage to lose. There are a few ways to do this now (for example jumping into empty space in the chasm definition above), but I'm sure there will be many more before all is said and done.

Well, that's it. (Up to) three more days. It should be an interesting weekend.

**Side note: **Apparently someone posted this project to the <a title="Reddit: Racket" href="http://www.reddit.com/r/Racket">Racket sub-Reddit</a>.

I was wondering where that random spike in traffic was coming from. :smile:

Quick disclaimer: The current series of posts is more about progress on the game and far less about how you might write a Roguelike in Racket. There is <a title="GitHub: House on the Hill source" href="https://github.com/jpverkamp/house-on-the-hill" rel="nofollow">source code</a> available on GitHub, but at the moment that's about it.

After 7DRL is over, I plan on going back and factoring out any code that might be useful for others to write Roguelikes into a PLaneT package in addition to writing a series of posts detailing how the guts of the project actually work (and all that I've learned about how to write OO code in Racket--and how not to).

So if you're interested in that part of it, stick around. I should get to it sometime next week.

&nbsp;
