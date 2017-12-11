---
title: Wombat IDE - Enter the bug tracker
date: 2011-08-26 05:05:08
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: enter-the-bug-tracker
---
Today saw another round of bug fixes:

* Internal swap of [] to () to make [Kawa](http://www.gnu.org/software/kawa/ "The Kawa Scheme Language") behave correctly (this is a hacky fix, I should figure out a better way to do this)
* Split the code for the REPL into seperate files for better organization
* Some sanity checks on bracket matching, preventing a few errors I was seeing


<!--more-->

Also, a few new features:

* Up/down arrow in the REPL now moves through the REPL history
* Added the ability to change the color of the various syntax options

One fairly big change I made was to give up on the options files that I'd previously mentioned. I'd originally liked the idea of using Scheme files as the actual options defintions, but the code to correctly load and save them was getting to be a bit hairy to maintain. So for now, the code has been changed to use the <a title="Java Preferences API" href="http://docs.oracle.com/javase/1.4.2/docs/guide/lang/preferences.html">Java Preferences API</a>. I'm not 100% sure this is how I'll keep it, but it seems to be working for now.

Also, I've started using the <a title="Issue Tracker" href="https://code.google.com/p/wombat-ide/issues/list">Issue Tracker</a> to keep track of things that I need to do. If there are any problems with Wombat or features that you'd like to see, please submit an issue. It's much easier not to forget things this way.

Since I don't think I've mentioned it, the source code is <a title="Wombat IDE Source Code" href="https://code.google.com/p/wombat-ide/source/checkout">available online</a>. Feel free to take a look!

The new build is r131, available <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>.