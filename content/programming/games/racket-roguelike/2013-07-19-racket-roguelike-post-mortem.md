---
title: 'Racket Roguelike: Post-mortem'
date: 2013-07-19 14:00:22
programming/languages:
- Racket
programming/sources:
- 7DRL
programming/topics:
- Games
- Roguelikes
series:
- Racket Roguelike
---
Almost four months ago, I started writing a series on how to write a roguelike in Racket. I believed then as I believe now that Racket is an excellent all around language and that I would like to see more done with it--particularly in games.

<!--more-->

That being said, it's about time to move on. It's been harder and harder to come up with new things to do and the weight of the code base is beginning to weigh against me (see below). In moving on though, it's time for one last last post detailing the good and the bad.

What went well:

* I learned a lot more about Racket--in particular its {{< doc racket "object system" >}} and {{< doc racket "GUI library" >}}
* I created a few libraries that may be useful in other projects (which I indend to convert to [PLaneT 2 packages](http://planet.racket-lang.org/) when it is released): 
* [ascii-canvas](https://github.com/jpverkamp/ascii-canvas) \-- a direct translation of [Trystan's AsciiPanel](https://github.com/trystan/AsciiPanel) for Java for creating simple ASCII displays
* [noise](https://github.com/jpverkamp/noise) \-- generate {{< wikipedia page="Simplex noise" text="Simplex" >}}or {{< wikipedia page="Perlin noise" text="Perlin" >}} noise
* [thing ](https://github.com/jpverkamp/thing)\-- an alternative prototype-based object system

</li>
	<li>The display looks pretty good for ASCII (much better than my original system for [House on the Hill]({{< ref "2013-03-12-the-house-on-the-hill-day-1.md" >}}))</li>
	<li>Other than [a break for getting married]({{< ref "2013-05-24-racket-roguelike-going-on-hiatus.md" >}}), I managed to keep up a weekly posting schedule</li>
</ul>
What went less than well:

* It's still not really a game; there's no end game / no way to win
* I never did compile it for distribution other than source code (I'm [still interested](https://groups.google.com/forum/#!topic/racket-users/LLB6oV1VsPo) in getting general cross compiling working)
* The [thing]({{< ref "2013-04-18-racket-roguelike-3-rats-rats-everywhere.md" >}}) system is powerful, but really I probably should just have stuck with Racket objects
* I haven't quite figured out how to organize Racket projects; the code base is messier than I like and getting harder to modify each week
* Performance isn't particularly great; this is partially based on generating tiles on the fly and just a general lack of optimization (I could have done this better)

Overall, not too bad. I'd like to start another game in Racket soon; this time perhaps something actually intended for distribution. I'm thinking about going back to [particle/sandbox based games]({{< ref "2009-11-28-sandbox-and-so-it-begins.md" >}}). It's been rather a while, but I still remember a good number of the optimizations. Plus, I'd like to see exactly how many other genres such techniques could be applied to. Puzzle games are obvious and have been done often enough before but what about top down or side view shooters? What about a platformer? Could be neat.

If you'd like to read from the beginning, have at it. Here are all of the posts:



As always, if you'd like to see all of the code for this project, you can do so on GitHub:
- <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike">Racket Roguelike</a>

If you'd like to try it yourself, you'll need to have both <a href="http://git-scm.com/">Git</a> and <a href="http://racket-lang.org/">Racket</a> and run the following series of commands:

```bash
git clone git://github.com/jpverkamp/racket-roguelike.git
cd racket-roguelike
git submodule init
git submodule update
racket main.rkt
```

**Edit:**

It seems that the submodules wondered off at some point. Instead, you can install the three libraries this uses directly using {{< doc racket "pkg" >}}, and then run the code:

```bash
raco pkg install github://github.com:jpverkamp/ascii-canvas/master
raco pkg install github://github.com:jpverkamp/noise/master
raco pkg install github://github.com:jpverkamp/thing/master
git clone git://github.com/jpverkamp/racket-roguelike.git
cd racket-roguelike
racket main.rkt
```

If anyone would like to take this code and develop it further, feel free. I just ask that you drop me a line and let me know what you're doing. I'd love to see it.
