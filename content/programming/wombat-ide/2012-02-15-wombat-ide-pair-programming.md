---
title: Wombat IDE - Pair programming
date: 2012-02-15 04:55:13
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
As I mentioned once before, I've been meaning to add the ability to share screens between different users. I spent a few hours yesterday evening, trying to get everything working correctly in the new setup. So far, I have messages sent and received (encoded using a <a title="Public Domain Base 64 library" href="http://iharder.sourceforge.net/current/java/base64/">Public Domain Java Base64 library</a>) between a host and one or more clients, all with an easy enough to use GUI built right into Wombat:

<!--more-->

{{< figure src="/embeds/2012/connect.png" >}}

If you click Host, you get a new document with a light green background that otherwise acts exactly like a normal document:

{{< figure src="/embeds/2012/host.png" >}}

And then if you join, you get another green box. Now, whatever you type in either box will be sent to both of them:

{{< figure src="/embeds/2012/join.png" >}}

While this example shows both text areas in the same Wombat session, it works exactly the same way with two different instances, either on the same machine or on different machines. The only problems comes up when you are trying to run the host on a machine with an outgoing firewall--particularly most Windows machines. We're trying to get an exception through the SoIC machines which should solve the problem for C211, but it's something to keep in mind otherwise.

If you want to switch over to the new versions of Wombat, you can get it <a title="Wombat Launcher Download" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>. You should have at least version 2.46.40.
