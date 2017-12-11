---
title: Wombat IDE - OSX Dock Icon
date: 2012-05-25 04:55:14
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
For the longest time, I've been having issues with the Dock Icon on OSX. It isn't set using the same code that works in Windows and Linux, but I think I've finally figured it out.

Using information from <a title="Java OSX Dock Icon and Name" href="http://alexlaird.net/2011/02/java-os-x-dock-icon-and-name/">this blog post</a>, I can use the `com.apple.eawt.Application` class to set the Dock Icon. It isn't set immediately on launch, but shortly thereafter. Not perfect, but close.