---
title: 'February #1GAM post-mortem'
date: 2013-03-01 14:00:33
programming/sources:
- One Game a Month
programming/topics:
- Games
---
Is it possible to write a post-mortem if you really only got about four hours into a game?

Well, let's hope so. That's all the further I've made it with this month's <a title="One Game A Month" href="http://onegameamonth.com/">#1GAM</a> a month--and it's pretty much entirely my fault. The whole idea was to start earlier in the month and spread out the work out a bit... That didn't happen.

<!--more-->

So how far did I get? Well, take a look.

{{< figure src="/embeds/2013/brong-lots-of-balls.png" >}}

My goal for this month was to right a smashup of [[wiki:Breakout (video game)|Breakout]]() and [[wiki:Pong]](). I don't know if I've ever actually written a version of either, so it seemed like a thing to do.

The basic gameplay would have started with a ball on each paddle with a solid wall of Breakout bricks between the two. To actually start scoring, you'd have to break through the wall. In addition, there was going to be the whole gamut of Breakout powerups: sticky paddles, speed changing balls, meteors, splitters, you name it. The power ups were going to (theoretically) play a large part in actually beating your opponent.

What I got isn't too bad. In about 4 hours, I managed to write code for balls and paddles using custom drawing and collision detection code. That was about when I realized that I *really* didn't want to write custom collision detection code again... So I went off in search of a physics library.

{{< figure src="/embeds/2013/brong.png" >}}

What I came down to was <a title="Box2D" href="http://box2d.org/">Box2D</a>. It's the physics engine behind such hits as <a title="Angry Birds" href="http://www.angrybirds.com/">Angry Birds</a>, so I figured it should be pretty solid. It took perhaps ten minutes to get everything installed (Box2D requires <a title="slf4j" href="http://www.slf4j.org/">slf4j logging library</a> which took a few minutes to figure out) and about half an hour after that until I had the balls bouncing around as happy as you please. That was nice.

The paddles took a bit longer. It took a bit to get them moving because I didn't want to thread the KeyEvents through everything. Instead, I ended up binding to the `KeyboardFocusManager` which got be raw `KeyEvent`s (and all three kinds in one listener as well!).

```java
KeyboardFocusManager manager = 
    KeyboardFocusManager.getCurrentKeyboardFocusManager();
manager.addKeyEventDispatcher(this);
```

It seems to work well enough. Just remember to return `false` if you want to use more than one of these at the same time.

After that though, I had to figure out how to make the paddles stay at the same height. As it was, they kept getting a bit of vertical movement when the balls hit them. At first, I just gave them a crazy high density. That worked for a bit, but I was still getting some drift. Eventually though, I stumbled onto <a title="Box2D manual" href="http://www.box2d.org/manual.html">Prismatic Joints</a>. Basically, they do exactly what I want: limit movement to one axis. It took a bit to figure out exactly *how* to hook them up though.

All together, I'm actually pretty happy with how far I made it, given the extremely limited amount of time I put into it. I could claim that I'm going to do better this month (and I really hope that I do), but only time well tell for certain. The decision I have now is whether to continue work on Brong or to move on to something else. I'm leaning towards the latter (not actually a fan of this sort of game), but I still do want to have written Pong/Breakout at some point. It's just something that you do. We'll see.