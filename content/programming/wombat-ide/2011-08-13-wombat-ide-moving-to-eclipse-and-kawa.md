---
title: Wombat IDE - Moving to Eclipse and Kawa
date: 2011-08-13 05:05:11
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: moving-to-eclipse-and-kawa
---
Two big changes for the project today. I've changed the IDE I'm using from <a title="Netbeans Java IDE" href="http://netbeans.org/">Netbeans</a> to <a title="Eclipse IDE" href="http://www.eclipse.org/">Eclipse</a>. Then, the back-end scheme system will be changing from <a title="Second Interpreter of Scheme Code" href="http://sisc-scheme.org/">SISC </a>to <a title="The Kawa Language Framework" href="http://www.gnu.org/software/kawa/">Kawa</a>.

<!--more-->

Personally, I have no gripe with <a title="Netbeans Java IDE" href="http://netbeans.org/">Netbeans</a>, I just have a lot more experience with <a title="Eclipse IDE" href="http://www.eclipse.org/">Eclipse</a>. Finally getting around to a full cross-platform deployment means that I need to know a little more about how to configure everything so that I can deploy successfully, preferably with as little hassle as possible. Since I have significantly more prior experience with Eclipse, I've moved over to that. As an added plus, it's already installed on all of the machines on campus, so I can easily work from pretty much anywhere syncing via subversion.

As I mentioned back in [And so it begins]({{< ref "2011-07-26-wombat-ide-and-so-it-begins.md" >}}), my choice for back-end was between SISC and Kawa. I went with SISC as it was much easier to embed, but the more that I worked with it, the less satisfied I was that it would be even close to compatible with the <a title="Chez Scheme Homepage" href="http://www.scheme.com/chezscheme.html">Chez</a> auto-grader that was previously developed. In order to better match Chez, I've moved to Kawa. Originally, I had issues with Kawa as an embedded language as it seems designed to be standalone, but after some experimentation with the system, I was able to make everything work. We'll see how this decision plays out in the long run, but for the moment, I believe it was the correct choice.

Minor bug fixes:

* It's now possible to open a new document after tearing off / closing the previous last document. The problem was a misunderstanding on my part in how the [docking window's](http://www.infonode.net/ "InfoNode Docking Windows") tabbed panes worked.
* The open document is saved before being run. Previously it would transparently load the code without checking for changes and might miss any unsaved changes. There's a disable-able confirmation if you actually meant to save the document or not.

The new build is available <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>, as always.