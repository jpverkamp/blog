---
title: The House on the Hill - Day 1
date: 2013-03-12 13:00:39
programming/languages:
- Racket
- Scheme
programming/sources:
- One Game a Month
programming/topics:
- Games
- Roguelikes
---
This week marks 2013's 7-day Roguelike (7DRL) challenge, a contest where entrants attempt to write an entire Roguelike in 7 days. Since I haven't started my #1GAM a month for March (and since my [successfully completed January game]({{< ref "2013-02-01-1gam-chesslike-1-0-did-it.md" >}}) was a Roguelike as well), it seems like the perfect opportunity to kill two birds with one stone.

<!--more-->

My idea is to base a Roguelike on the excellent board game <a title="Betrayal at House on the Hill" href="http://boardgamegeek.com/boardgame/10547/betrayal-at-house-on-the-hill">Betrayal at House on the Hill</a>. In that game, up to six ostensibly ordinary men and women (and occasionally children) venture into the eponymous 'house on the hill' and set out to explore it. The rooms are randomly placed each game, making the house exceedingly strange at times, but the best part comes halfway through.

At a semi-random point in each game, one of the players will trigger the Betrayal. When that happens, one or more of the players (or occasionally none at all) will become the Traitor. They will be given a new set of rules and goals, directly opposing all non-Traitor players. There's a wonderful us-versus-them mechanic for the second half of the game. It's not always (or not even often) balanced, but it's definitely interesting, particularly since neither side can actually be sure of the other's rules.

I'm not sure how much of that us-versus-them feeling I can get out of five days (I won't be able to work much next weekend if at all), but I'm going to at least get down the dynamic (and hopefully creepy) feeling of the house. The best part of the house is the dynamic layout, so that's one thing I'm definitely working hard on. To that end, I wrote a dynamic plugin system for rooms that should be flexible enough for just about anything that would be possible in the original game (and more!).

To showcase what I have, here's an example of one of the room definitions (it's written in <a title="The Racket Language" href="http://racket-lang.org/">Racket</a>, a cousin of Scheme/Lisp, but don't be scared off by all the parenthesis :smile: ):

```scheme
(define-room 
  #:name "Chasm"
  #:description ""
  #:floors '(basement)
  #:doors '(west east)
  #:floorplan 
  '("         "
    "         "
    "         "
    "||| |||||"
    "|||||| ||"
    "|||||||||"
    "         "
    "         "
    "         ")
  #:tiles
  (list 
   (define-tile
     #:tile #\space
     #:name "empty space"
     #:description "a seemingly endless drop into darkness"
     #:walkable #t
     #:onWalk 
     (lambda (player tile)
       (and (.ask "Are you sure you want to step into the empty space?")
            (.kill player "You fall screaming into the abyss."))))
   (define-tile
     #:tile #\|
     #:name "rickety bridge"
     #:description "half rotten planks of wood; they look like they might break at any moment"
     #:walkable #t
     #:onWalk
     (lambda (player tile)
       (.set tile (+ 1 (.get tile 'steps 0)))
       (define steps (.get tile 'steps 0))
       (cond
         [(and (>= steps 5) (> (random) 0.5))
          (.kill player "The step beneath you gives way, plunging you into the endless abyss.")]
         [(or (= steps 2)
              (and (> steps 2) (> (random) 0.5)))
          (.say "The step beneath you creaks, threatening to give way at any moment.")])))))
```

The basic idea here is that all of the room definitions are source code files in their own right which can be dynamically loaded. So you can add any sort of dynamic behavior that you want. In this case, we have dynamic behavior in the `#:onWalk` events, both for the 'empty space' of the chasm and the 'rickety bridge' hanging over it.

In the first case, the game will warning you if you try to walk out into space. If you don't heed the warning--game over. In the latter, it will keep track of how many times you hit each step. After enough times, there's an ever increasing chance that you'll plunge to your doom!

I'm not sure how much I'm going to change / expand the API by the time I'm done, but I think this is a pretty solid start. Any additional changes should be much easier since the basic groundwork is already done.

Goals for Day 2:

* Figure out how to draw the game to the screen in Racket
* Generate random rooms, lining up the doorways

I'll be cross posting this series both on <a title="jverkamp.com" href="http://blog.jverkamp.com">my personal blog</a> and on the <a title="7DRL BLog" href="http://7drl.org/">7DRL blog</a>. If you'd like to see the source code, it's available <a href="https://github.com/jpverkamp/house-on-the-hill" title="House on the Hill source">on GitHub</a>. Theoretically, I'll have an initial download (or at least screenshots) in the next day or two. If everything goes perfectly (which it rarely does, but one can hope), I'll have a web-based version as well, using <a title="Whalesong: a Racket to JavaScript compiler" href="http://hashcollision.org/whalesong/">Whalesong</a>. I've never used it before, so we'll see how that goes. :smile:
