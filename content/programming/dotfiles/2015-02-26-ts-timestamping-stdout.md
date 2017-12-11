---
title: 'ts: Timestamping stdout'
date: 2015-02-26
programming/languages:
- Python
programming/topics:
- Dotfiles
- Open Source
- Unix
---
Loving data as much as I do, I like to [optimize]({{< ref "2013-04-16-adventures-in-optimization-re-typed-racket.md" >}}) things. To make sure I'm actually going the right way, it's useful to time things. While it's trivial in most languages to add timing, it's even easier if you don't have to.

<!--more-->

To that end, here is `ts`, a tool for adding timestamps to each line of `stdin`:

```python
#!/usr/bin/env python3

import sys
import time

def stamp(line):
    now = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
    sys.stdout.write('{0} {1}\n'.format(now, line.strip('\n')))
    sys.stdout.flush()

stamp('--- <ts> ---')

for line in sys.stdin:
    stamp(line)

stamp('--- </ts> ---')
```

For example:

```bash
$ python long-running-script.py | ts

[2015-02-25 17:05:35] --- <ts> ---
[2015-02-25 17:05:35] things
[2015-02-25 17:05:43] stuff
[2015-02-25 17:05:53] all done
[2015-02-25 17:05:53] --- </ts> ---
```

Whee!

If you'd like to download this or any of my other [dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}}), you can do so on on GitHub: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/ts">ts</a>.
