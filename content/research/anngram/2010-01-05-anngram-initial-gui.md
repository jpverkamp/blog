---
title: AnnGram - Initial GUI
date: 2010-01-05 05:05:55
programming/languages:
- .NET
- C#
programming/topics:
- Computational Linguistics
- Natural Language Processing
- Neural Networks
- Research
---
**Overview**

Basically, I got tired of modifying the command line every time I wanted to test new values.  To that end, I spent a small bit of time coding up a GUI to make further experiments easier.

<!--more-->

Lessons learned:

* Windows Forms designer doesn't work well if you aren't using Visual Studio
* GTK is rather powerful, but also rather complicated
* GTK# doesn't hide enough of the underlying complexity of GTK
* Windows Forms (without designer) are easy enough to use and cross platform (via Mono)

**GUI**

**{{< figure src="/embeds/2010/AnnGram-examples-1.png" >}}**

The left and right trees each show all of the documents that have been loaded into the system, sorted by author.  Right-click either tree to load additional documents.  Clicking an author or document selects it for comparison.  Once two items have been selected, the differences (right now only cosine difference) are displayed in the central area.  The previous results are not cleared to aid in comparison.  Above are three visible examples, marked A, B, and C:

* A: All of Shakespeare versus As You Like It
* B: All of Shakespeare versus all of William Blake
* C: All of Shakespeare versus the Book of Genesis

The values are the same one displayed last time from the command line version.

For future versions, additional values will be displayed beneath the cosine similarity so that they can be compared.