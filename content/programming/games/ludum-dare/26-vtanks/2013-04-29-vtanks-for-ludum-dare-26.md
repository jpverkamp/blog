---
title: VTanks for Ludum Dare 26
date: 2013-04-29 12:30:36
programming/languages:
- Flash
programming/sources:
- Ludum Dare
- One Game a Month
programming/topics:
- Games
- Vectors
---
So when I got home, I decided that I really didn't want to miss another Ludum Dare. Granted, there was only about two hours left in the competition. I'm good, but I'm not that good. :smile:

Also, I really wanted to make a web-based game, which meant either write another game in Java (suboptimal) or learn how to write a game in Flash or JavaScript. Nothing like a last minute decision to use an unfamiliar framework and write a game in less than 24 hours. :smile:

In the end, I did it in six.

<!--more-->

(If you want to skip ahead, here's a link to play the game: <a title="VTanks" href="http://apps.jverkamp.com/games/vtanks/">VTanks</a>)

For anyone unfamiliar, the goal of Ludum Dare is to take a theme and make a game. The rules are <a title="Ludum Dare competition rules" href="http://www.ludumdare.com/compo/rules/">here</a>, but basically you have 48 hours to write everything from scratch (code, music, and graphics) and create an entire game around a theme. This time around? The theme is minimalism. A bit strange of a theme--doesn't every Ludum Dare tend towards minimalism of necessity?--but it seems like a decent first chance.

I had a few ideas. Perhaps something based on [[wiki:Conway's game of life|Conway's Game of Life]](), maybe a platformer. Perhaps something based on particle systems (like my old Sandbox code, I should work on that some day...). Or perhaps the idea I finally with, let's make a version of [[wiki:Scorched Earth (computer game)|Scorched Earth]]().

Basically, you have a tank. You can control the angle and power of your cannon and you're trying to destroy the other tanks. Perhaps a more modern version would be [[wiki:Worms (computer game)|Worms]](), there have been a few of those.

Next, an art style. To make it minimal, we'll just have vector graphics. None of those fancy, schmancy pixel graphics the original game with[^1], just straight boring lines.

Finally, a toolkit. As I mentioned, I wanted to be able to deploy to the web. So JavaScript or Flash. I've done a tiny bit of the former and basically none of the latter, so of course Flash it was. I've heard great things about <a title="FlashDevelop" href="http://www.flashdevelop.org/">FlashDevelop</a> as an IDE and <a title="Haxe programming language" href="http://haxe.org/">Haxe </a>as a programming language. It really does seem that you could write one, run anywhere (even on mobile devices) and something about that intrigues me.

So off into Haxeland!

There's a lot I could say about Haxe.

Pro: it's a nice language, borrowing the same functional features that ActionScript (Flash) has with both a solid enough type system and type inferring that didn't annoy me too much (although you have to be careful with numbers sometimes).

Con: It's not a Scheme, but I think for the time being I can live with that. :smile: Perhaps I can figure out how to compile Scheme/Racket code to Haxe? Not today though. :)

Pro: The IDE is nice, with decent auto-completion support and nice multi-document tabbing and error highlighting.

Con: I miss hitting Ctrl-Space on errors and getting fixes for them (like Eclipse). Also the auto-completion was obsessed with using the `browser` namespace rather than the `nme` one, even when I'd already imported the latter. That should be fixable. Also I don't like curly braces on the next line, but I think it's starting to see my way. :smile:

So, how did I do?

Well, I have a game. It's not much of one, granted. There's no title screen, no music, no game over. But there are four tanks that you can play and they can destroy each other until finally someone ones. So it counts. :smile: I'm not expecting much in the way of rankings, but the point is to learn and the point is to finish. So job well done.

Here's some screenshots:

{{< figure src="/embeds/2013/vtanks.png" >}}

Starting out, a nice mountain[^2] landscape and four tanks, battling for supremacy.

{{< figure src="/embeds/2013/vtanks-fire.png" >}}

Fire in the hole! Even the explosions are color coded. :smile:

{{< figure src="/embeds/2013/destruction.png" >}}

A bit later and there are some nice craters going on.

{{< figure src="/embeds/2013/game-over.png" >}}

Bam. Game over. Unfortunately, you have to reload the page to restart, but that's something I could fix, along with a title page and some music. As of this writing, there's still another 14 or so hours left in the Jam. At this point though, I think I'm done. I've learned what I wanted to learn and perhaps can turn that knowledge into something bigger in the future. And it is technically a game, albeit barely.

Anyways, if you want to, you can check out the game right here, right now. Perhaps it's worth a minute or two of your time. See you again in 4 months for Ludum Dare 27!

# <a title="VTanks" href="http://apps.jverkamp.com/games/vtanks/">Play VTanks now</a>

(If you're interested, here's my contest entry link: <a href="http://www.ludumdare.com/compo/ludum-dare-26/?action=preview&uid=19702">VTanks by jpverkamp</a>)

[^1]: Although I'd love to make something combining Sandbox and Scorched Earth. That'd be cool...
[^2]: You have no idea how many times I misspelled that word...