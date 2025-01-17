---
title: Wombat IDE - The return of screen sharing
date: 2012-08-31 04:55:46
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
I've been working the last few days to get screen sharing [working again]({{< ref "2012-02-15-wombat-ide-pair-programming.md" >}}) and I think I have something. Again. Hopefully. The first idea was to use a UDP [[wiki:multicast]]() network but when router configuration on campus got in the way, I moved back to a more direct TCP-based system. Still, I think it works pretty well.

<!--more-->

**UDP Multicast**

The goal in the UDP Multicast based system was to create a multicast group that all of the machines connected to a given router could connect to. Since the IP and port of this network would be set, the documents could be identified by any generated name (theoretically), making unique and non-confusing names a non-issue for anyone using the software. Unfortunately, it seems that the networks on IUs campus (where Wombat is primarily deployed) don't actually forward UDP packets. Perhaps I should have checked this before trying it, but so it goes. It did help conceptually towards the new TCP-based version thought.

**TCP Client/Server**

The next idea was to go back to a more traditional client/server based TCP architecture. Similar to how I ended up working with it last time, the goal is to have any machine capable of acting as either a server or a client so that we don't have to depend on a central server. I did do a better time of writing the framework this time with actual separate client and server code for easy of implementation rather than the previous framework which had either one code base with some optional features for the server that got a bit hard to maintain at times.

In any case, here's how it works (and it does seem to work):

{{< figure src="/embeds/2012/connect-button.png" >}}

First, choose the connect button from the toolbar.

{{< figure src="/embeds/2012/sharing-dialog.png" >}}

After that, choose create a new document or join (if someone's already created one). By default, the disconnect button will be grayed out, but once you have a document open you can use this button to turn it from a shared document back into a traditional single user one.

{{< figure src="/embeds/2012/new-document.png" >}}

Once you have a shared document, you can tell two ways. First, the document name will appear in the title bar of the document. In this case, the document is named `wKiZNZQ+`. To join, you'll need either that same ID or the host  IP and port you are connecting to. It turns out that ID above actually encodes the IP and port, it's just a Base64 encoding of those 6 bytes. Second, the background will be a light shade of green rather than the traditional white. For some reason, the green doesn't appear on some small fraction of Windows 7 machines that I've tested on and I'm not sure why, but the document name will always appear.

In any case, it seems to be working well enough for me in testing, so go ahead and give it a spin. Technically, it should work anywhere that you can access a port, so if you have a public IP you could theoretically share a document across the world.

As one last bit of warning, there are a few gotchas that you might want to watch out for at the moment:

* Typing at the same time can do strange things; essentially it will stay in sync but your cursors might move while you're typing. Just try to avoid it for the time being.
* Enabling [lambda mode]({{< ref "2012-02-17-wombat-ide-upload-button-and-lambda.md" >}}) on one machine but not another will cause oscillations in the document. For the moment, either should just have it enabled or not.
* Sending a lot of keystrokes in a very short period of time can freeze up the display. The server will continue to work, but the display might stop updating. At normal (or even pretty quick) typing speeds, this shouldn't be an issue, nor will it be an issue cutting/pasting large amounts of code as those are sent as a single packet.

With this new update, Wombat is now at version 2.243.15. As always, you can download the latest version <a title="Wombat IDE Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a> or let the version you've already downloaded update itself.