---
title: Wombat IDE - Big fixes and confusion removal
date: 2011-11-02 04:55:05
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
A small list of bug fixes first:

* Updated `draw-tree` to use ovals instead of rectangles to match the old version
* Fix error messages with functions whose names end with `?`
* Added better error messages for division by 0, particularly for the function `/`
* Removed whitespace at the ends of files and lines on save
* Fixed automatic indentation on the first line of a file
* Removed formatting from the undo/redo stack (as it's automatic anyways)


<!--more-->

Next, there are a few functions that have been confusing students, mostly because they aren't actually Scheme functions, but rather parts of the Scheme/Java bindings. Specifically, member? (not analogous to member) and integer (type casting).

Finally, there's a new dialog added for find/replace. It works pretty much how such features always work, allowing sequential or global search and replace of given strings in the currently open file. It works well enough for now, although I'm not particularly happy with the interface:
{{< figure src="/embeds/2011/find-replace.png" >}}
The new version is <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/ ">1.305.1</a>.