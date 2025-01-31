---
title: "Wombat IDE - \u03BB mode"
date: 2012-02-24 04:55:55
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: wombat-ide-lambda-mode
---
I've fixed the λ-mode that I was talking about [earlier]({{< ref "2012-02-17-wombat-ide-upload-button-and-lambda.md" >}}), adding a menu option so that all `lambda`s will automatically be exchanged for λs or vice versa. Behind the scenes, files are always saved with the word `lambda` (so that the macro in the previous post isn't actually necessary), but such changes should be completely transparent to the end user.

If you want to switch over to the new versions of Wombat, you can get it <a title="Wombat Launcher Download" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>. You should have at least version 2.54.6.
