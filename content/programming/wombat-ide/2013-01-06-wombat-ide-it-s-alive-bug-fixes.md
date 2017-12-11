---
title: Wombat IDE - It's Alive! (bug fixes)
date: 2013-01-06 14:00:29
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
It's alive!

I haven't worked on Wombat in a while, but with the new semester quickly approaching, I figured that it would be a good time to take out a few of the outstanding bugs on the <a title="Wombat IDE Issue Tracker" href="https://code.google.com/p/wombat-ide/issues/list">issue tracker</a>. Granted, there's still a fair few, but it's a start.

<!--more-->

Specifically, the following bugs have been closed:

* [Issue 170](https://code.google.com/p/wombat-ide/issues/detail?id=170 "Wombat IDE - Issue 170") \- Command history will be saved and loaded across separate runs
* [Issue 186](https://code.google.com/p/wombat-ide/issues/detail?id=186 "Wombat IDE - Issue 186") \- Documents with the same name and different folders will now be saved correctly in recent documents
* [Issue 190](https://code.google.com/p/wombat-ide/issues/detail?id=190 "Wombat IDE - Issue 190") \- The extra space before the first line of output for any command has been removed
* [Issue 195](https://code.google.com/p/wombat-ide/issues/detail?id=195 "Wombat IDE - Issue 195") \- Brackets (originating) in comments will no longer be matched
* [Issue 201](https://code.google.com/p/wombat-ide/issues/detail?id=201 "Wombat IDE - Issue 201") \- Added a C211 CSV library ([API](http://blog.jverkamp.com/wombat-ide/c211-csv-api/ "Wombat IDE - \(c211 csv\) API"))
* [connect dialog]({{< ref "2012-08-31-wombat-ide-the-return-of-screen-sharing.md" >}})
* [Issue 209](https://code.google.com/p/wombat-ide/issues/detail?id=209 "Wombat IDE - Issue 209") \- Empty commands in the REPL will no longer cause infinite loops
* [Issue 214](https://code.google.com/p/wombat-ide/issues/detail?id=214 "Wombat IDE - Issue 214") \- Hiding and revealing a [tree](http://blog.jverkamp.com/wombat-ide/c211-tree-api/ "\(c211 tree\) API") will no longer cease to redraw
* [Issue 215](https://code.google.com/p/wombat-ide/issues/detail?id=215 "Wombat IDE - Issue 215") \- Java errors no longer leak through on [images](http://blog.jverkamp.com/wombat-ide/c211-image-api/ "\(c211 image\) API") with a 0 dimension

Hopefully I'll have some time to hammer out a few of the bigger issues in the near future. It's nice to be back to coding again.

With the new year, I'll also be bumping the version number to 3.x, which makes the new build 3.6.24. If you'd like to download the newest version of Wombat, you can grab it <a title="Wombat IDE Launcher" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>.

In particular, I'm hoping to actually tackle a few of these:

* [Issue 142](https://code.google.com/p/wombat-ide/issues/detail?id=142 "Wombat IDE - Issue 142") \- Figure out how to configure the campus network to allow shared documents
* [Issue 204](https://code.google.com/p/wombat-ide/issues/detail?id=204 "Wombat IDE - Issue 204") \- Add a mirror site for updates/downloads in case tank goes offline
* [Issue 210](https://code.google.com/p/wombat-ide/issues/detail?id=210 "Wombat IDE - Issue 210") \- Deal with occasional remaining zombie Petite processes
* [Issue 213](https://code.google.com/p/wombat-ide/issues/detail?id=213 "Wombat IDE - Issue 213") \- Update the c211 libraries to use *define-record-type*

We'll see how that goes.

If you're a Wombat user and have any issues in particular you'd like me to prioritize, feel free to drop me a comment below or submit an issue on the <a title="Wombat IDE Issue Tracker" href="https://code.google.com/p/wombat-ide/issues/list">issue tracker</a>.