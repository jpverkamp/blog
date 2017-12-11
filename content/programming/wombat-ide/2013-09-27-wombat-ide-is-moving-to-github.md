---
title: Wombat IDE is moving to GitHub
date: 2013-09-27 04:55:51
programming/languages:
- Java
- Scheme
programming/topics:
- GitHub
- Google Code
- Version Control
series:
- Wombat IDE
---
Since the rest of my code is hosted on GitHub, I figured that I probably should move Wombat IDE there as well.

To that end, we've moved from <a href="https://code.google.com/p/wombat-ide/">Google Code: wombat-ide</a> to <a href="https://github.com/jpverkamp/wombat-ide">GitHub: jpverkamp/wombat-ide</a>.

<!--more-->

The first part of the change was the source code and version control history. This actually went relatively straight forward. All I had to do was clone the code to a local machine, pull down all of the branches, replace the 'origin' repository, and push. Now, anyone can clone the new repository in much the same way as the old, just with the new URL:

```bash
git clone git@github.com:jpverkamp/wombat-ide.git
```

The harder part was moving the issues. There are ways to automatically convert issues, but in the five minutes I allowed, I couldn't get them to run. Any more time than that and it would just be easier to manually convert them--which is what I ended up doing. The following open issues have been moved to GitHub (preserving as much of the comment history as I could/felt necessary):

* [Issue 65](https://code.google.com/p/wombat-ide/issues/detail?id=65) → [#1](https://github.com/jpverkamp/wombat-ide/issues/1) (Parenthesis Highlighting in Text Highlighting)
* [Issue 97](https://code.google.com/p/wombat-ide/issues/detail?id=97) → [#2](https://github.com/jpverkamp/wombat-ide/issues/2) (Comments in strings)
* [Issue 115](https://code.google.com/p/wombat-ide/issues/detail?id=115) → [#3](https://github.com/jpverkamp/wombat-ide/issues/3) (Code Crunching)
* [Issue 141](https://code.google.com/p/wombat-ide/issues/detail?id=141) → [#4](https://github.com/jpverkamp/wombat-ide/issues/4) (Bug report button)
* [Issue 142](https://code.google.com/p/wombat-ide/issues/detail?id=142) → [#5](https://github.com/jpverkamp/wombat-ide/issues/5) (Fix document sync)
* [Issue 143](https://code.google.com/p/wombat-ide/issues/detail?id=143) → [#6](https://github.com/jpverkamp/wombat-ide/issues/6) (Document replay)
* [Issue 150](https://code.google.com/p/wombat-ide/issues/detail?id=150) → [#7](https://github.com/jpverkamp/wombat-ide/issues/7) (Wombat for iuanyware?)
* [Issue 152](https://code.google.com/p/wombat-ide/issues/detail?id=152) → [#8](https://github.com/jpverkamp/wombat-ide/issues/8) (Live coding)
* [Issue 173](https://code.google.com/p/wombat-ide/issues/detail?id=173) → [#9](https://github.com/jpverkamp/wombat-ide/issues/9) (Procedure completion in edit window)
* [Issue 174](https://code.google.com/p/wombat-ide/issues/detail?id=174) → [#10](https://github.com/jpverkamp/wombat-ide/issues/10) (Toolbar on drawing window)
* [Issue 177](https://code.google.com/p/wombat-ide/issues/detail?id=177) → [#11](https://github.com/jpverkamp/wombat-ide/issues/11) (Pause/resume capability during live-display)
* [Issue 181](https://code.google.com/p/wombat-ide/issues/detail?id=181) → [#12](https://github.com/jpverkamp/wombat-ide/issues/12) (Java 7 x64 issue)
* [Issue 183](https://code.google.com/p/wombat-ide/issues/detail?id=183) → [#13](https://github.com/jpverkamp/wombat-ide/issues/13) (Add update-* to c211 libraries)
* [Issue 185](https://code.google.com/p/wombat-ide/issues/detail?id=185) → [#14](https://github.com/jpverkamp/wombat-ide/issues/14) (Find and Replace)
* [Issue 194](https://code.google.com/p/wombat-ide/issues/detail?id=194) → [#15](https://github.com/jpverkamp/wombat-ide/issues/15) (Prompted to save file on exit)
* [Issue 198](https://code.google.com/p/wombat-ide/issues/detail?id=198) → [#16](https://github.com/jpverkamp/wombat-ide/issues/16) (red is not red)
* [Issue 199](https://code.google.com/p/wombat-ide/issues/detail?id=199) → [#17](https://github.com/jpverkamp/wombat-ide/issues/17) (Turtle graphics freaks out on +nan.0)
* [Issue 200](https://code.google.com/p/wombat-ide/issues/detail?id=200) → [#18](https://github.com/jpverkamp/wombat-ide/issues/18) (Log files on Unix based systems)
* [Issue 204](https://code.google.com/p/wombat-ide/issues/detail?id=204) → [#19](https://github.com/jpverkamp/wombat-ide/issues/19) (Mirror site for download)
* [Issue 205](https://code.google.com/p/wombat-ide/issues/detail?id=205) → [#20](https://github.com/jpverkamp/wombat-ide/issues/20) (Verify that all files have been downloaded successfully)
* [Issue 208](https://code.google.com/p/wombat-ide/issues/detail?id=208) → [#21](https://github.com/jpverkamp/wombat-ide/issues/21) (Pencil Tool changes document)
* [Issue 210](https://code.google.com/p/wombat-ide/issues/detail?id=210) → [#22](https://github.com/jpverkamp/wombat-ide/issues/22) (Pressing stop button initiates increased CPU consumption.)
* [Issue 212](https://code.google.com/p/wombat-ide/issues/detail?id=212) → [#23](https://github.com/jpverkamp/wombat-ide/issues/23) (Support for regular expressions in find and find-replace)
* [Issue 213](https://code.google.com/p/wombat-ide/issues/detail?id=213) → [#24](https://github.com/jpverkamp/wombat-ide/issues/24) (define-record-type in c211 libraries)
* [Issue 216](https://code.google.com/p/wombat-ide/issues/detail?id=216) → [#25](https://github.com/jpverkamp/wombat-ide/issues/25) (jumpy left margin in Wombat)
* [Issue 217](https://code.google.com/p/wombat-ide/issues/detail?id=217) → [#26](https://github.com/jpverkamp/wombat-ide/issues/26) (Add some configuration options to version file)
* [Issue 218](https://code.google.com/p/wombat-ide/issues/detail?id=218) → [#27](https://github.com/jpverkamp/wombat-ide/issues/27) (Wombat command-line history saving)
* [Issue 222](https://code.google.com/p/wombat-ide/issues/detail?id=222) → [#28](https://github.com/jpverkamp/wombat-ide/issues/28) (read-csv)
* [Issue 228](https://code.google.com/p/wombat-ide/issues/detail?id=228) → [#29](https://github.com/jpverkamp/wombat-ide/issues/29) (Syntax highlighting confused by ;#|)

And that should be it. I've changed the old Google Code repository so that it shouldn't be trivial to submit issues or see the code there, but rather have links to the new content. If anyone has any issues with it, please let me know either in the comments here or by email: <a href="mailto:wombat-ide@jverkamp.com">wombat-ide@jverkamp.com</a>