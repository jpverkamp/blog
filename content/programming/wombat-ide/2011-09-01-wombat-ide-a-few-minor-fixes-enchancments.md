---
title: Wombat IDE - A few minor fixes/enchancments
date: 2011-09-01 04:55:35
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: a-few-minor-fixesenchancments
---
There are just a few end of the month bug fixes and enhancements this time:

* (Hopefully finally) fixed the long standing [Issue 2](https://code.google.com/p/wombat-ide/issues/detail?id=2 "Issue 2: Automatic indentation sometimes gets out of sync"): Automatic indentation sometimes gets out of sync
* Added a recent documents menu
* Added an option to reset custom color scheme to the default
* Fixed an issue where the program wouldn't close if text was waiting to be displayed


<!--more-->

One bigger addition was that the bracket matcher now colors mismatched brackets as shown here (there is a closing parenthesis against an opening square bracket):

{{< figure src="/embeds/2011/Wombat-build-167.png" >}}

The new build is r167, available at the <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">usual link</a>.