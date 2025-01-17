---
title: Wombat IDE - Stopping and syntax editing
date: 2011-09-02 04:55:55
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: stopping-and-syntax-editing
---
A few new features today in <a title="Wombat IDE" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">r170</a>, a stop button and a dialog to select syntax options.

First, the stop button. There's one thing that I've been meaning to work on for quite a while: the ability to stop code that is currently running. To that end, I've added a new button to the interface (highlighted below) that will do exactly that. At the moment, pretty much all that it does is request that the currently running <a title="The Kawa Language Framework" href="http://www.gnu.org/software/kawa/">Kawa</a> thread will stop. It isn't perfect, but it's better than nothing.

<!--more-->

{{< figure src="/embeds/2011/stop-button.png" >}}

Since I haven't done this yet, I'll go ahead and go through all of the buttons available. From left to right, the first block is New, Open, Save, and Close. The next set are Run (which will run the current file using `load`, shortcut defaults to F5), Stop, Format (which will auto-indent your code, shortcut defaults to F6), and Reset (which will reset the Scheme environment to the default one, for example if you accidently `(define + -)`). As a side note, the Icons are from a set available for free use (see below).

Here's an example of the automatic formatting:

{{< figure src="/embeds/2011/format-before.png" >}}

{{< figure src="/embeds/2011/format-after.png" >}}

Usually, this shouldn't be necessary. The same formatting will be applied just as you type. But if you copy/paste code (for example), this will fix the formatting for you to whatever indentation you have defined in the syntax dialog.

Speaking of which, the syntax dialog:

{{< figure src="/embeds/2011/syntax-dialog.png" >}}

Essentially, it's just a list of keywords, each with an indentation value (the default is 2). The interesting part was working with the <a title="Java: JTable API" href="http://docs.oracle.com/javase/6/docs/api/javax/swing/JTable.html">Java Swing JTable API</a>, making it so that all changes to the table were automatically synchronized with the back-end data structure. It's not a style of coding that I'm particularly used to, but it seems like it will definitely be something interesting to have learned.

<span style="text-decoration: underline;">Icon License:</span>

<a title="Link to Icon Download Page" href="http://www.freeiconsweb.com/Free-Downloads.asp?id=607">http://www.freeiconsweb.com/Free-Downloads.asp?id=607</a>

LED Icon Set v1.0 are designed for web designers/developers by Marcis Gasuns,  Siberia. These .png icons make a professionally looking icon set and are  totally free.

You can do whatever you want with these icons (use on web or in desktop  applications) as long as you don't pass them off as your own and remove this readme file. A credit statement and a link back to <a title="Required Iconset Link" href="http://led24.de/iconset/">http://led24.de/iconset/</a> or <a title="Required Iconset link" href="http://led24.de/">http://led24.de/</a> would be appreciated.