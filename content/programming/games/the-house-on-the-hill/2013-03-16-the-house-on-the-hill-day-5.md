---
title: The House on the Hill - Day 5
date: 2013-03-16 14:00:39
programming/languages:
- Racket
- Scheme
programming/sources:
- One Game a Month
programming/topics:
- Games
- Roguelikes
---
Not much in the way of screenshots today, but I did manage to add quite a lot of framework for content (which I'm going to spend tomorrow fleshing out). Now, the player has four stats (Might, Vigor, Intellect, and Sanity; I don't think those were the original stats but I don't have a copy at the moment to check). Each of them starts at a random value from 2 to 5. If any reaches 0, game over.

Also, to actually make use of said stats, there are two new kinds of definitions that you can stick in the data folder to automatically be used by the game: events and items.

<!--more-->

Events are automatically triggered when you enter a room for the first time. Eventually, this will include all manner of spooky happenings, but at the moment there are only two: Bite and Helpful Item. Here's the definition for Bite:

```scheme
(define-event
  [name "Bite"]
  [text "A growl, the scent of darkness.
Pain. Darkness. Gone."]
  [effect
   (lambda (player)
     (define player-roll (roll (send player get-stat 'might)))
     (define bite-roll (roll 4))
     (cond
       [(and (< player-roll bite-roll) (zero? (random 2)))
        (send player say "The bite tears at your flesh. You feel weaker.")
        (send player stat-= 'might 1)]
       [(< player-roll bite-roll)
        (send player say "The bite stings. Is that normal?\nSuddenly you feel tired.")
        (send player stat-= 'vigor 1)]
       [else
        (send player say "The bite hardly seems worth mentioning.\nYou shrug it off.")]))])
```

The name and text will be displayed to the player (at the moment in a message dialog; tomorrow I'm going to figure out how to display these as an overlay in the ASCII instead). Then the effect will take place. In this instance, the player will roll against some monster in the darkness. If the player wins, nothing happens. If they lose, they'll take a hit to either Might or Vigor. 

Helpful Item, as one might suspect, generates a random item and gives it to the player. Right now, there's only one item: the Book.

```scheme
(define-item
  [name "Book"]
  [text "A diary or lab notes? 
Ancient script or modern ravings?"]
  [on-gain
   (lambda (player)
     (send player stat+= 'intellect 2))]
  [on-loss
   (lambda (player)
     (send player stat-= 'intellect 2))])
```

Each item has an event for when you gain it and when you lose it right now, but I'll probably add ones for `on-attack` and `on-defend` to make things like weapons and armor make more sense. I'm just not sure how that's going to work out yet.

That's all I have. We're running right up against the deadline, but it's definitely a game at this point--albeit not really a very fun one--so I think I'll call that a win. Doesn't mean I won't put a few more hours into it this weekend.