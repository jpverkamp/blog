---
title: Wombat IDE - Busy day for small changes
date: 2012-03-27 04:55:51
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
Bug fixes:

* [Issue 138](https://code.google.com/p/wombat-ide/issues/detail?id=138 "Issue 138"): Automatically create a backup file (with a ~ suffix) on save and an option to disable it. There have been a few issues with Wombat crashing that I haven't managed to track down, this should help people recover from those. (They're rare; as in 2 cases reported among over 150 students for several months, so this shouldn't happen to the majority of users).
* The mnemonic in the recent documents menu has been tweaked to be ascending and 1 based rather than descending and 0 based.
* Fixed an issue where occasionally hitting `enter` in the REPL wouldn't run the current code based on incorrect bracket matching.
* `list->image` and `image->list` are not properly highlighted as keywords.


<!--more-->

Other enhancements:

* Licenses have been added to all source code. The project itself is licensed under the [GPL v3](https://www.gnu.org/copyleft/gpl.html "GPL v3") (it has to be because of the InfoNode code; that's a topic for another time), but the source code itself has been released under the [3-clause BSD license](http://www.opensource.org/licenses/bsd-3-clause "3-clause BSD License").
* [Issue 86](https://code.google.com/p/wombat-ide/issues/detail?id=86 "Issue 86"): I finally got line numbers along the left side working; see below for a screen shot. At some point, I managed to fix the line sizing issues that I was having, although I don't recall exactly when.
* [Issue 129](https://code.google.com/p/wombat-ide/issues/detail?id=129 "Issue 129"): Added a new syntax definition file rather than storing the syntax in the Java Preferences with the rest of the options. This will make automatically updating it much easier.

Example of the new line numbers:

{{< figure src="/embeds/2012/line-numbers.png" >}}

You shouldn't have to do anything other than let Wombat update to get the new version. If you have at least 2.86.4, you already have it. If you don't already have Wombat, you can download the launcher <a title="Wombat Launcher Download" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>.