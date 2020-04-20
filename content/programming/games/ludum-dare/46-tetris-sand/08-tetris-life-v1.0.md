---
title: "LD46: Tetris Life v1.0"
date: 2020-04-19 20:30:00
programming/languages:
- GScript
- Godot
programming/sources:
- Ludum Dare
programming/topics:
- Cellular Automata
- Physics
- Games
series:
- Ludum Dare 46
---
<iframe width="320" height="640" style="border: 1px solid black;" src="/embeds/games/ludum-dare/46/v1.0/launcher.html"></iframe>

Controls:

- Left and right to move the block and forth
- Z and X to rotate it (or crash into things)
- If a block gets stuck, you can hit ENTER to lock it in place
- ESC to quit the current level

Goals: 

- To win: Get the plants to the top of the level
- To lose: Kill off all of the plants #keepitalive

And there you have it. This page will serve as the main entry for Ludum Dare. If you'd rather download an executable for Windows/OSX/Linux, you can do so on the GitHub release page:

- [GitHub: Tetris Life v1.0](https://github.com/jpverkamp/tetris-life/releases/tag/v1.0)

Speaking of which, per the Ludum Dare rules (and because I would have anyways), the full source code:

- [GitHub: Tetris Life source](https://github.com/jpverkamp/tetris-life/)

MIT Licensed. I would appreciate a comment if you do anything cool with it. 

Some updates since last time:

- Music!
- More elements!
- Polish!

<!--more-->

They say a picture is a thousand words, so here's about a million:

<video controls src="/embeds/2020/ludum-dare-46-final.mp4"></video>

# Music

I made some music! I have and vaguely know how to use GarageBand, so I mostly threw something together:

{{< figure src="/embeds/2020/ludum-dare-46-music.png" >}}

Best song ever? Nah. But it's kind of fun and not bad for less than half an hour. I want to play with GarageBand more now.

<audio controls src="/embeds/2020/ludum-dare-46.mp3" >

# More elements

I threw in a few more `Experimental` elements: Acid, Wax, Ice, and Rainbow. I'm not going to go into much detail, but suffice it to say it only took about 10 minutes each to add them. The engine is pretty flexible like that. And no performance hits. 

# Polish

The last things to do were polish and publish. To polish, I implemented/cleaned up a help system and a few more options:

{{< figure src="/embeds/2020/ludum-dare-46-polish-1.png" >}}

{{< figure src="/embeds/2020/ludum-dare-46-polish-2.png" >}}

# Publish

I'm still hosting the HTML5 version on this blog, but I didn't want to commit all the binaries. But I can use GitHub releases for exactly that! Godot made this *really* easy. 

{{< figure src="/embeds/2020/ludum-dare-46-publish.png" >}}

I tested the HTML5, OSX, and Windows (via Wine) versions, but I have no doubt they all work. Pretty cool.

And... that's it. I'll probably write up a post mortem tomorrow along with reviewing a slew of games. This was pretty awesome. I want to write all the games now!

# Blog posts

If you'd like to see my full post series, you can use the links to the left or here's a list:

{{< taxonomy-list "series" "Ludum Dare 46" >}}