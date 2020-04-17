---
title: Generated HTML index
date: 2012-10-06 14:00:12
programming/languages:
- HTML
- Python
programming/topics:
- Web Development
---
A simple script today to generate an HTML index listing all of the files in a given directory. This has come in handy in the past when Apache has had `Options -Indexes` set (disabling their automatically generated indexes) and I didn't have the permissions to override it.

<!--more-->

If you want to follow along, you can get the full source code [here](https://github.com/jpverkamp/small-projects/blob/master/blog/html-index.py).

Easy enough to use, first here's the usage (which you can also get with `html-index help`):

```bash
Usage: html-index [short|long|force|all]
  force - overwrite old index.htm without asking
  help - display this message and exit
  long (default) - links <li>[here](https://github.com/jpverkamp/small-projects/blob/master/blog/html-index.py).

If you find this helpful, be sure to let me know in the comments below. :smile:
