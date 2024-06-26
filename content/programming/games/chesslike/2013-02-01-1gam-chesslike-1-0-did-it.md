---
title: '#1GAM - ChessLike 1.0 - Did it!'
date: 2013-02-01 14:00:24
programming/languages:
- Java
programming/sources:
- 7DRL
- One Game a Month
programming/topics:
- Chess
- Games
- Roguelikes
---
Well there you have it. Three days to a feature complete game.

I ended cutting one of the kinds of levels, but other than that I got everything that I wanted in the game. It's got 10 different kinds of pieces, 8 different kinds of levels (most procedurally generated), and statistics galore. It actually turned out to be kind of fun, although it's a bit slower than I'd like. Not much I can do about that though without implementing a mouse interface (which I'll probably do some day).

<!--more-->

In any case, here are some screen shots of the final product (or you can just skip to the links at the end and play it for yourself!):

{{< figure src="/embeds/2013/main-menu.png" >}}

First we have the main menu. Simple enough. Let's hit `[Enter]` to start a game.

{{< figure src="/embeds/2013/level-1.png" >}}

Here's the first level. The idea is that you start on out in a Forest and then head down into some caves. Over on the right there you can see the stairs leading downwards (in white) and there are currently four enemy pawns standing in your way. Pawns can only attack diagonally and otherwise only move orthagonally, so they're pretty easy to hunt down.

If you want to, you can just run right by the pawns and go ahead down into the caves. But if you capture them all, you'll get a reward (without the rewards, it's almost impossible to beat the game).

{{< figure src="/embeds/2013/level-2.png" >}}

If you head down, you reach the first set of underground levels--the caves. Here you can see there there are two exits: green and white. The white one always leads you to the next level deeper and the colored ones lead to special levels. In this case, an Underground Forest. You'll just have to check that out for yourself. Be warned though--with just a King, the special levels can be a bit tricky.

Here too, you can see the first other piece: a bishop (in the lower right). Although you can't see it here, all pieces are limited to a maximum range of up to four tiles in any direction. I made this change after realizing just how hard it was to corner any of the pieces with unlimited movement (like Rooks and Bishops).

Also, there are two keys of interest that will work on any screen: F1 and F2.

{{< figure src="/embeds/2013/help-menu.png" >}}

Pressing F1 will bring up this nice help screen. It tells you all of the pieces, the rules, and all of the other controls. Hopefully it's easy enough to figure out what you have to do with just this.

{{< figure src="/embeds/2013/stats-menu.png" >}}

And pressing F2 will bring up the statistics. Unfortunately, the applet version doesn't have the proper permissions to do this, so you'll get a blank screen instead. But if you download and run the JAR version, it should persist your settings across any number of runs. Roguelike players love statistics after all. :smile:

(Yes, I cheated. I was testing something in the Throne Room, so I skipped right to it.)

And that's all I have. This is my January #OneGameAMonth and it's done (for the time being). I may put out a final bug-fix version (particularly if I can work around the statistics bug), but that's probably about it. Other than that, it's onwards to bigger and better things! The plan is to start earlier this month, but you all know how that will likely work out...

Also, I've decided to put ChessLike up on GitHub. You can see the full source <a href="https://github.com/jpverkamp/chesslike" title="GitHub: ChessLike">here</a>. I'm not 100% sure about the license yet, but it will probably be one of the standard [[wiki:copyleft]]() ones.

{{< figure link="http://apps.jverkamp.com/chesslike/ChessLike-1.0.4.htm" src="/embeds/2013/Launch ChessLike 1.0.4" >}}

{{< figure link="http://apps.jverkamp.com/chesslike/" src="/embeds/2013/Launch the newest version" >}}
