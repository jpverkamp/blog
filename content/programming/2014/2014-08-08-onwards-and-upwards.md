---
title: Onwards and upwards
date: 2014-08-08 00:05:00
---
Huh. Things suddenly look a bit different around here, don't they?

Long story short, I finally finished a project that I've been working on off and on for the better part of two years: converting my blog to a static website.

<!--more-->

For years, I've been running this blog on a custom <a href="http://wordpress.org/">Wordpress</a> installation, first on <a href="https://www.ipower.com/">ipower</a> and then on <a href="http://www.dreamhost.com/">dreamhost</a>. That works well enough (and is certainly easier to get started), but eventually (especially as you add plugins) it just starts getting slower and slower.

And that makes you think... Why? It's not like my blog content is actually dynamic[^1]. So why do I constantly re-render the content? There are caching plugins galore for Wordpress, but even those can only do so much. Why not go old-school[^2]? Purely a collection of static content.

Once I decided to do that, the next step was to find a static blog generator. Luckily, this isn't exactly a new idea. There are a whole pile of options out there. Here are a few that I spent at least a good amount of time looking into:


* [Jekyll](http://jekyllrb.com/) \- Ruby + Liquid, MIT licensed
* [Octopress](http://octopress.org/) \- Ruby + Liquid, MIT licensed, runs Jekyll under the hood
* [Pelican](http://blog.getpelican.com/) \- Python + Jinja2, GPL
* [hyde](http://hyde.github.io/) \- Python + Jinj2, conceptually based on Jekyll
* [frog](https://github.com/greghendershott/frog) \- Racket + Markdown, MIT licensed


The Ruby ones are a little less good for me personally, since when I first was learning a language of that ilk, the choice was basically Python or Ruby. I choose Python. I've been meaning to learn Roby, but don't have nearly enough experience to tune a blog generator nearly as much as I want.

The next problem was that none of them worked. Seriously, I tried installing each, writing a number of conversion scripts (starting with the excellent <a href="https://github.com/thomasf/exitwp">exitwp</a>) to push my posts into shape, but nothing worked. Either I couldn't get the page to build at all or I couldn't get anywhere near what I thought would be a good starting point.

So I did what any other sane[^3] person would do. I built my own!

As you may have noticed, I write a lot of Racket code. I've drunk the functional language Kool-aid, but I like having 'batteries included', so Racket just works. As mentioned, there's at least one static blog generator written in Racket already: <a href="https://github.com/greghendershott/frog">frog</a>. It's a great project (and it could actually build my blog from the ground up), but it doesn't quite have any of the more powerful functionality I was looking for. Most specifically, plugins. Even static, I want my site to be as powerful/dynamic as it can be... but without rewriting html over and over again. So I took the general idea and off I went....

... two years later ...

It's finally done. What you're reading now is built by my own <a href="https://github.com/jpverkamp/blog-generator">blog-generator</a>[^4]. It takes in a pile of more or less Markdown + {{< doc racket "at expressions" >}}, runs them through a bunch of plugins, and spits out a giant pile of static html content.

That being said, I'm sure I missed something. If you notice anything, I'd love to hear about / fix it. Let me know below / email me at <a href="mailto:me@jverkamp.com">me@jverkamp.com</a>.

Eventually, I'll probably write up a few posts about how exactly the blog generator works (and some of the problems I ran into writing it), but for now, I just want to get it up.

Keep an eye out for any changes:

* [@jpverkamp](https://twitter.com/@jpverkamp)
* [RSS](/feed/)

[^1]: Other than posting new posts, or a few client-side examples.
[^2]: Relatively speaking
[^3]: For some definitions of sanity...
[^4]: Need a better name for that at some point.