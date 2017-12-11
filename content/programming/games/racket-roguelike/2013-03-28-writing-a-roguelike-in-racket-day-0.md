---
title: Writing a roguelike - in Racket! (Day 0)
date: 2013-03-28 15:00:49
programming/languages:
- Racket
programming/sources:
- 7DRL
programming/topics:
- Games
- Roguelikes
---
Back when I finished [my 7DRL]({{< ref "2013-03-17-the-house-on-the-hill-postmortem.md" >}}), I said that I was going to try to write a full tutorial series on writing a Roguelike in Racket, modeled somewhat on Trystan's excellent series in Java: <a title="roguelike tutorial 01: Java, Eclipse, AsciiPanel, application, applet" href="http://trystans.blogspot.com/2011/08/roguelike-tutorial-01-java-eclipse.html">roguelike tutorial 01: Java, Eclipse, AsciiPanel, application, applet</a>.

<!--more-->

Well, it's about that time. Technically, I'll be starting next week. But to get that far, I wanted to make the ascii-canvas that I was working on finished and really solid so that I could actually have nice pictures throughout and not worry about working on both the framework and the tutorial at the same time.

So to that end, I present <a title="ascii canvas source on GitHub" href="https://github.com/jpverkamp/ascii-canvas">ascii-canvas</a>:

{{< figure src="/embeds/2013/random-tiles.png" >}}

Basically, I gave up for the moment on using fonts directly and fell back to a more traditional sprite sheet as a code page. This will also allow for a sort of tile graphics, albeit with a hard limit (at the moment) at 256 characters ((I haven't actually tried a larger image...)). Here's the image that I'm using for testing:

{{< figure src="/embeds/2013/cp437_16x16.png" >}}

Anything in white will be drawing in the foreground color, anything in magenta will use the background color. My goal is to support grayscale images eventually with appropriate tinting, but that's not currently supported.

The API is actually identical [ChessLike]({{< ref "2013-02-01-1gam-chesslike-1-0-did-it.md" >}}), so I'm already familiar with it. Plus, it's really straight forward to write. All you have to deal with is clear, write for single characters, write-string for strings, and write-center for centered strings. There's no automatic line feeds like some libraries have, but that would be entirely possible to add in the future.

To show off a bit of what it can do, here are a few examples:

First, we just write out all of the currently possible characters:

```scheme
(for* ([xi (in-range 16)]
       [yi (in-range 16)])
  (define c (integer->char (+ xi (* yi 16))))
  (send test-ac write c xi yi))
```

{{< figure src="/embeds/2013/all-chars.png" >}}

* * *

Next, let's color them. You can add either just the foreground or the foreground and background colors. Any color can be specified either as a color string (see the {{< doc racket "color database" >}} for a full list) or using `make-color` with `RGB`. Here's a nice gradient example:

```scheme
(for* ([xi (in-range 16)]
       [yi (in-range 16)])
  (define c (integer->char (+ xi (* yi 16))))
  (send test-ac write c xi yi (make-color (* xi 16) (* yi 16) 0)))
```

{{< figure src="/embeds/2013/all-chars-colored.png" >}}

* * *

After that, we can play a moment with simple centered strings (with foreground and/or background colors): 

```scheme
(send test-ac write-center "this is a test" 10)
(send test-ac write-center "this is a test in blue" 11 "blue")
(send test-ac write-center "this is a test in blue on yellow" 12 "blue" "yellow")
```

{{< figure src="/embeds/2013/first-test.png" >}}

* * *

And finally, we have some nice screen corruption with randomly placed and colored characters appearing around the screen:

```scheme
(thread
 (lambda ()
   (let loop ()
     (send test-ac write 
           (integer->char (random 256)) 
           (random 40) (random 20) 
           (make-color (random 256) (random 256) (random 256))
           (make-color (random 256) (random 256) (random 256)))
     (sleep 0.1)
     (loop))))

(thread
 (lambda ()
   (let loop ()
     (send test-frame refresh)
     (sleep 0.5)
     (loop))))
```

{{< figure src="/embeds/2013/random-tiles.png" >}}

* * *

Or you could just run them all at once:

{{< figure src="/embeds/2013/all-tests-later.png" >}}

* * *

I think the most impressive example was taking the code and converting <a href="https://github.com/jpverkamp/house-on-the-hill" title="House on the Hill source on GitHub">House on the Hill</a> to use it (click the image to embiggen):

{{< figure src="/embeds/2013/hoth-new-canvas.png" >}}

It took about 20 minutes to convert everything (and I got to learn about Git submodules in the process!), most of which consisted of flipping the arguments to the draw/write functions so the character/string was first. Here's a diff if you're curious: <a href="https://github.com/jpverkamp/house-on-the-hill/commit/2f6f71479963fbc3714ebe2f093dadcd742b6ae0" title="Diff when converting House on the Hill to the new ascii-canvas">commit 2f6f7147</a>. And dang does it look nicer. You can actually sort of see what's going on, as opposed to some of the old images when half the characters were larger than the tiles. 

If you decide to download the <a href="https://github.com/jpverkamp/house-on-the-hill" title="House on the Hill source on GitHub">House on the Hill source</a>, make sure you run `git submodule update`. For whatever reason, Git doesn't pull down submodules by default (which will do a pretty good job of breaking things). 

That's all I have today, but now that's out of the way--full speed ahead!