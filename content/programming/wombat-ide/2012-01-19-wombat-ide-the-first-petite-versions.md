---
title: Wombat IDE - The first Petite versions
date: 2012-01-19 04:55:40
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
I started the basic conversion to petite back on 13 January, but I finally managed to get everything working today. To start the conversion, the first thing that I did was split everything into three active projects:

* ide - contains the GUI code and code to whatever Scheme system I use
* launcher - contains the code to find the correct version of the IDE and launch it and also to update to the latest version(s) automatically
* petite - contains the bindings to Petite and can actually act as a stand-alone command-line REPL


<!--more-->

At the moment, the Petite bindings can successfully detect the operating system that you are using (either Windows, Linux, or OSX) and will look for a directory with a matching names which the launcher is responsible for downloading and extracting. The OSX and Linux versions were easy enough to fetch as I could extract them directly from the archive while in the case of Windows, I had to run the installer to get a working version. It took a bit to track down the necessary files (I need the main executable and the boot file) but everything seems to be working just fine now.
After quite a bit of fussing around (and a bit more trouble that I'd like) the first versions of Wombat with Petite are working. It's not perfect, but it's getting there. At the moment, most people should stick with what will likely be the last Kawa/Webstart based version at <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">1.346.13</a>, but hopefully I'll have the new version stable enough for use soon enough.