---
title: Sampling stdin
date: 2012-09-22 14:00:15
programming/languages:
- Python
---
A relatively simple script today. When I was working with Twitter data, it quickly became apparent that it's a *lot* of data. So I needed some way that I could reduce the amount of data that I was dealing with while still keeping many of the same properties. To that end, I wrote a really simple script that would forward lines from `stdin` to `stdout` but would only do so a given percentage of the time.

<!--more-->

That's really all there is to it. I present to you `sample`:

```python
import random, sys

# get the chance
# use exceptions for sanity checks
try:

    if len(sys.argv) != 2: raise Exception()
    chance = float(sys.argv[1])
    if chance < 0 or chance > 1: raise Exception()
except:
    print('''Usage: sample [chance]

Forward [chance] percentage of stdin to stdout
[chance] must be in the range [0,1]''')
    sys.exit(0)

# now just read line by line and output
# based on that random chance
for line in sys.stdin:
    if random.random() < chance:
        print(line[:-1])
```

Generally, you'd pipe the output of another command to it. It's not smart enough to act like most scripts where you can either read a file or pipe input, but that's something that could easily be added with something like this:

```python
# arg[0] is the program name, arg[1] is the chance
read = False
for arg in sys.argv[2:]: 
    with open(arg, 'r') as fin:
        for line in fin:
            if random.random() < chance:
                print(line[:-1])
```

You will need to tweak the error checking, but that's not so hard to do. Some testing (I have the simple version of this program in my path as '`sample`'):

```
┌ ☺ <span style="color: purple;">verkampj</span>@<span style="color: orange;">minty</span> <span style="color: green;">~</span>
└ cat sample.py | sample 0.1

for line in sys.stdin:

┌ ☺ <span style="color: purple;">verkampj</span>@<span style="color: orange;">minty</span> <span style="color: green;">~</span>
└ cat sample.py | sample 0.1

import sys
    chance = float(sys.argv[1])
    print('''Usage: sample [chance]
```

If you find it useful, let me know. I'm sure there are all sorts of time when you may want to look at just a representative sample where such a script would come in handy. 

You can download the full source here: <a href="https://github.com/jpverkamp/small-projects/blob/master/scripts/sample.py" title="sample source code">sample source code</a>