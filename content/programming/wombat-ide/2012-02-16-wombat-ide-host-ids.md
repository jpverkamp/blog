---
title: Wombat IDE - Generated host IDs
date: 2012-02-16 04:55:43
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
Just a small change, now a short (8 character) alpha-numeric string will be used whenever a user hosts a connection, rather than just having to enter the IP and port combination:

<!--more-->

{{< figure src="/embeds/2012/hosted-string.png" >}}

Theoretically, this will help with adaption as this is what the students are already used to when they use other screen sharing systems such as <a title="TypeWith.me homepage (based on EtherPad)" href="http://typewith.me">typewith.me</a> or any of the other systems based on <a title="EtherPad homepage" href="http://etherpad.com/">EtherPad</a>. Also, if the back-end changes from a direct connection to a multicast based system (or the like), the I don't have to change the front end--hopefully to minimize confusion.

If you want to switch over to the new versions of Wombat, you can get it <a title="Wombat Launcher Download" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>. You should have at least version 2.47.24.