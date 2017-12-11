---
title: Wombat IDE - Docking windows
date: 2011-07-26 05:15:55
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: docking-windows
---
One of the features that I really wanted to have in Wombat was the ability to have multiple documents in separate windows with the ability to drag them around both in their parent window or out of it, docking as necessary. Most modern IDEs have this feature and I figured that I should make Wombat as easy to use and like the others as I could. I looked around somewhat at different options for docking windows in Java and ended up settling on <a title="InfoNode Docking Windows" href="http://www.infonode.net/">InfoNode Docking Windows</a>, available under the <a title="GPL v3" href="http://www.gnu.org/copyleft/gpl.html">GPL v3</a>. It took some work to adapt to their API, but within a few hours I was able to release another build, r87 using the new system, available <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>.

<!--more-->

{{< figure src="/embeds/2011/Wombat-build-87.png" >}}

As you can see, the REPL and History windows are now dockable, along with any open documents. This allows the user to either attach the REPL to the open window or detach it and put it on a second monitor (for example) if they choose. I was somewhat impressed with how well the InfoNode windows worked with the project.