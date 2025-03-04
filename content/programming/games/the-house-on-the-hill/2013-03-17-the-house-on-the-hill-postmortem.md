---
title: The House on the Hill - Postmortem
date: 2013-03-17 14:00:14
programming/languages:
- Racket
- Scheme
programming/sources:
- One Game a Month
programming/topics:
- Games
- Roguelikes
---
It turns out that I won't have any time this weekend after all. So technically, I have another day, but I'm not going to be able to finish this in 7 days. This actually works out, since in hindsight I don't think that Betrayal at House on the Hill's mechanics actually translate quite as directly to a Roguelike as at first I thought.

<!--more-->

This has definitely not been a waste of time, however. One thing that I set out to do--and that I think went quite well--was to use a language that I'm rather a fan of but isn't particularly widely used: <a title="Racket" href="http://racket-lang.org/">Racket</a>. So far as I can tell, there's a particular dearth of tools for writing games in general in Racket and Roguelikes in particular (although there are bindings for <a title="sdl4racket on PLaneT" href="http://planet.racket-lang.org/display.ss?package=sdl4racket.plt&amp;owner=pb82">SDL</a> and <a title="gl-world on PLaneT" href="http://planet.racket-lang.org/display.ss?package=gl-world.plt&amp;owner=jaymccarthy">OpenGL</a>, I've not had any luck getting either working). So this has been more of an exercise in figuring out how it could be done and documenting that experience.

In that case, my next goal will be to take what code I have and wrap it up in a nice package suitable for <a title="PLaneT Package Repository" href="http://planet.racket-lang.org/">PLaneT</a> (or potentially its successor, depending on how well that has progressed since last I looked) and write up a tutorial series along the lines of <a title="Trystan's blog: roguelike tutorial" href="http://trystans.blogspot.com/2011/08/roguelike-tutorial-what-and-why.html">Trystan Spangler's excellent example</a>. If that's the sort of thing that you're interested in, stick around (or subscribe via <a title="RSS Feed" href="http://blog.jverkamp.com/feed/">RSS</a>, <a title="jpverkamp on Twitter" href="http://twitter.com/jpverkamp">Twitter</a>, <a title="Subscribe via Feedburner email " href="http://feedburner.google.com/fb/a/mailverify?uri=jverkamp-blog">email</a>). I probably won't have it ready early next week yet, but it shouldn't be too long.

If you'd like to download what code I did get done, you can <a title="House on the Hill on GitHub" href="https://github.com/jpverkamp/house-on-the-hill">download it from GitHub</a>.