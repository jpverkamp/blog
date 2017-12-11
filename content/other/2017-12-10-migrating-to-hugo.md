---
title: Migrating to Hugo
date: 2017-12-10
programming/languages:
- Go
- Python
programming/topics:
- Hugo
---
A long time ago[^1], in a galaxy far, far away[^2], I [moved my blog]({{< ref "2014-08-08-onwards-and-upwards.md" >}}) from WordPress to a custom written static blog generator in Racket. And for a while, all was well.

<!--more-->

Then, about a year and a half ago now, I just stopped blogging. It wasn't that I didn't have anything left to say. I have a huge backlog of posts.

Mostly, I just got tired of the time it took to rebuild the blog and add new features.

Since then, every month or two, I would decide that I was going to rewrite my blog generator--again. Or I would move to one of the dozens[^3] of static blog generators out there. I wanted something that was fast (with then nearly and now over a thousand blog posts) and easy enough to modify for my variety of interests. Something that could display [programming posts](/programming/), [albums from Flickr](/photography/), [book/movie reviews](/reviews/), and various [writing exercises](/writing/). And anything else I might want to add in the future.

Long story, short, I eventually settled on [Hugo](https://gohugo.io/). It's a static blog generator written in Go, which I have some experience with through work. It's fast (with caching, it can rebuild my entire blog in a second or two). And it's relatively flexible[^4].

It took longer than I probably should have to write [a script](https://github.com/jpverkamp/blog/blob/e4aab2c/scripts/import-old-blog.py) to convert my old blog to the new format. I'll probably write a post or two about that eventually[^5]. Of particularly interest are a pair of import script for [Flickr](https://github.com/jpverkamp/blog/blob/e4aab2c/scripts/import-flickr.py) and [Goodreads](https://github.com/jpverkamp/blog/blob/e4aab2c/scripts/import-goodreads.py) so that I can automatically import new albums/reviews without having to copy/paste.

For now though, I hope this will be enough to get me blogging again. I've already retroactively added in all of the Flickr albums, Goodreads reviews, and a few other things that I've done in the last year and a half.

If you have any comments/suggestions, feel free to drop a line below or shoot me an email. I'm always glad to hear them.

[^1]: Well, four years.
[^2]: California. Might as well have been.
[^3]: Hundreds? How many of the silly things are there?
[^4]: Or at least by now I've figured out how to hammer it into shape.
[^5]: I never did write about my [Racket blog generator](https://github.com/jpverkamp/blog-generator)...
