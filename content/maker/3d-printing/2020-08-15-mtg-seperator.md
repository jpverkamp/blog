---
title: MtG Seperator
date: 2020-08-15
---
Finally getting around to the ['more of this']({{< ref "2020-02-22-sock-and-underwear-drawer" >}}) I mentioned. 

A little while back, I got a 3D printer (a Creality Ender 3, they're a really good budget option). It took forever and a day to tune it, but now that it's working, I've been printing various things I've found online. One of those things was some 3D Magic the Gathering (MtG) boxes. With those, I really wanted some dividers ([like these](https://www.thingiverse.com/thing:644763)), but instead of by color, I wanted them by set. 

{{< figure src="/embeds/maker/mtg-seperator/in-use.jpg" >}}

I know, I know.[^oldschool][^kroog]

Links:

* [Tinkercad (Tempest)](https://www.tinkercad.com/things/37VySqqpD6e-mtg-seperator/edit)
* [STLs for the sets I needed](/embeds/maker/mtg-seperator/mtg-seperator-stls.zip)

<!--more-->

This time around, I went simple and designed the card back in [Tinkercad](https://www.tinkercad.com/). It is browser based, but it worked pretty quickly, which is what I wanted. 

And the design is very simple. It's a 1mm thick sheet the size of a MtG card, with a tab at the top made of a solid rectangle and angled squares that cut away the corners. 

{{< figure src="/embeds/maker/mtg-seperator/with-corners.png" >}}

The only interesting bit was the symbols--but one reason I went for Tinkercad is that you can import SVGs, which is exactly what I did. 

{{< figure src="/embeds/maker/mtg-seperator/with-tempest.png" >}}

Pull in an SVG of the set symbol, extrude it slightly out, save as STL. I then loaded them into [Cura](https://ultimaker.com/software/ultimaker-cura) to slice them into gcode and send them to my printer. The raised bits, I colored with a sharpie. Looks pretty good to me!

Actually, what I did (because I'm that sort of geek) was to write a quick scraper against [Scryfall](https://scryfall.com/sets/) that would download the page source, find all SVGs, and name them with the associated text. If/when I find that script, I'll link it here, but since I expect the symbols themselves are probably copyrighted[^copywritten] and/or trademarked, so I will not directly upload them at this time. (I'm not 100% sure about the derivative works below, but let's go with it for now.)

[The STLs I generated]((/embeds/maker/mtg-seperator/mtg-seperator-stls.zip)) include Alliances, the Dark, Ice Age, Mirage, Portal Second Age, Stronghold, Tempest, Unglued, Urza's Saga, and Visions. I'm happy to generate any more if you would like me to, just [send me an email](mailto:blog@jverkamp.com). 

[^oldschool]: Yes, I know those are very old sets. I actually used to play more than a decade ago. I started around the Odyssey (2001) block and stopped buying packs after the first set in Mirrodin (2003, how the time flies), although for a while, I still played. After that, I played [MtG: Online](https://magic.wizards.com/en/mtgo) for a while and just recently tried the new the newer [MtG: Arena](https://magic.wizards.com/en/mtgarena). These cards though, I actually acquired from family when they bought a new house. Weird times. 

[^kroog]: Man there are some weird MtG cards. 

[^copywritten]: Fun fact, despite the fact that most works people are familiar with are written works, the verb is not copywrite so the past tense is not copywritten.