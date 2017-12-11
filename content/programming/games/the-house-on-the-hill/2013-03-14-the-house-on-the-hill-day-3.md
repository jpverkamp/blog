---
title: The House on the Hill - Day 3
date: 2013-03-14 14:00:04
programming/languages:
- Racket
- Scheme
programming/sources:
- One Game a Month
programming/topics:
- Games
- Roguelikes
---
Today I've made it to where I optimally would have been back on Monday, had I actually planned what I was going to do (and not changed ideas and frameworks literally as I was starting to work).

<!--more-->

I present to you:

{{< figure src="/embeds/2013/generated-rooms.png" >}}

As I was hoping yesterday, I have a player that moves and I have (most of) the rendering code. I haven't actually randomly selected the room, but the map of room coordinates and the random room selector are ready, I just have to be able to validate that everything connects nicely.

Unfortunately, it's a little sluggish at the moment, mostly do to the way that I'm drawing. Each time the screen has to update, it loops through each tile on the screen (top to bottom, left to right) and figures out if it's a room or border. For rooms, it figures out which room and then which tile. For non-rooms, it has to figure out which doors to place (which isn't entirely working as you can see). None of this is cached. So just in that screenshot above, I have something like 315 room lookups, each on a *hash* (not a *hasheq*; that matters).

That could easily be made better by looping across the rooms instead and drawing their 9x9 tiles before moving on. That would improve the runtime but at the cost of being somewhat more complicated codewise. It would also give me the ability to not draw the borders around rooms that don't exist yet though, which would be nice. I'll probably do this tomorrow, although it's going to take a bit. *Fingers crossed* for no more than an hour.

Then I've got monster / event content for Thursday and a bunch of item definitions for Friday. The nice thing about the structure is that all of my room definitions are dynamically loaded (as I mentioned Monday). So anything I stick in the *data/rooms *folder will just work™. Or at least that's the theory anyways. Should be an interesting few more days.