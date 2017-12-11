---
title: Regex search and replace
date: 2014-07-31
programming/languages:
- Python
programming/topics:
- Dotfiles
- Open Source
- Unix
---
Another random task that I find myself doing distressingly often: performing a regular expression search and replace recursively across a bunch of files. You can do this relatively directly with tools like `sed`, but I can never quite remember the particularly flavor of regular expression syntax `sed` uses.

<!--more-->

So instead, here's a version that uses Python regular expressions:

```python
#!/usr/bin/env python

import re
import sys

if len(sys.argv) < 3:
	print('Usage: re {pattern} {replacement} [file(s)]')
	sys.exit()

in_place_mode = '-i' in sys.argv
if in_place_mode: sys.argv.remove('-i')

pattern, replacement = sys.argv[1:3]
files = sys.argv[3:]
if not files: files = ['-']

for file in files:
	if file == '-':
		fin = sys.stdin
	else:
		fin = open(file, 'r')

	text = fin.read()
	fin.close()

	text = re.sub(pattern, replacement, text)

	if in_place_mode:
		fout = open(file, 'w')
	else:
		fout = sys.stdout

	fout.write(text)

	if in_place_mode:
		fout.close()
```

Quick and simple. It will open the file, read it in, replace, and save it back out. One neat trick is that you can read from `stdin` / write to `stdout` all relatively transparently.

As with all of my [dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}}), you can see the entire source on GitHub: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/re">re</a>.
