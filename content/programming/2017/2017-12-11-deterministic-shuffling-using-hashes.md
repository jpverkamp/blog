---
title: Deterministic Shuffling Using Hashes
date: 2017-12-11
programming/languages:
- Python
programming/topics:
- Dotfiles
- Hashes
- Sorting
---
Whenever I create my [yearly reading list]({{< ref "2017-01-01-reading-list.md" >}}), I need a way to order the books. Sure, I could just shuffle them normally, but that leads me to the temptation of cheating and re-shuffling them so that the books I want to read most are first. What I really need is a shuffle that will shuffle the same way every time.

Enter: hashsort

<!--more-->

The basic idea is to take a list of items, hash each of them, and sort them based on the hash values.

```python
import fileinput

inputs = set()

for line in fileinput.input():
    line = line.strip()
    if line:
        inputs.add(line)

hashed = {(hash(line), line) for line in inputs}

for _, line in sorted(hashed):
    print(line)
```

Unfortunately, the built in `hash` function isn't deterministic (I think it has something to do with memory addresses?):

```bash
$ python3 -c 'print(hash("test"))'

7048182159058774479

$ python3 -c 'print(hash("test"))'

7534055093572699423
```

So we need a custom `hash` function. While we're at it, let's deal with multiple possibly input types:

```python
import hashlib

def hash(line):
    if isinstance(line, bytes):
        pass
    elif isinstance(line, str):
        line = line.encode()
    else:
        line = repr(line).encode()

    hasher = hashlib.md5()
    hasher.update(line)
    return hasher.hexdigest()
```

That always uses {{< doc "python" "hashlib.md5" >}} to sort the lists. The [[wiki:md5]]() hash has some issues from a security perspective, but for our purposes here it works just fine. Let's try it out:

```bash
$ cat fruit

Apple
Banana
Cherry
Dragonfrut
Elderberry
Fig
Grape
Huckleberry
Kiwi

$ hashsort fruit

Grape
Elderberry
Fig
Huckleberry
Dragonfrut
Cherry
Apple
Banana
Kiwi
```

And no matter how many times you run it with the same input, you'll get the same values. Even better, if you add more values, they won't change the existing order, they'll just be inserted somewhere in the list:

```bash
$ echo 'Lime' >> fruit

$ echo 'Mango' >> fruit

$ hashsort fruit

Grape
Elderberry
Mango
Fig
Huckleberry
Dragonfrut
Cherry
Lime
Apple
Banana
Kiwi
```

That's pretty cool.

But what if I still want to cheat and have some little control over the 'random' ordering? Well, {{< doc "python" "hashlib" >}} has a small pile of hash functions. Let's add the ability to list what's available and choose one:

```python
import argparse
import hashlib
import sys

algorithms = {algorithm.lower() for algorithm in hashlib.algorithms_available}

parser = argparse.ArgumentParser()
parser.add_argument('--hash', default = 'sha256', choices = algorithms, help = 'Hash to set, any hash in hashlib can be used')
parser.add_argument('--list', action = 'store_true', help = 'Display available hashes and exit')
parser.add_argument('files', metavar='FILE', nargs='*', help='Files to read, if empty use stdin')
args = parser.parse_args()

if args.list:
    for algorithm in sorted(algorithms):
        print(algorithm)
    sys.exit(0)
```

{{< doc python argparse >}} is pretty wonderful when it comes to creating simple UNIX style applications. In this case, we'll generate the list of algorithms using {{< doc python "hashlib.algorithms_available" >}} and both give them as an {{< doc python argparse >}} `choices` parameter (which will warn the user if they specify one not on the list) and also as a separate `--list` parameter, which lets us do this (I use the [Fish shell](https://fishshell.com/)):

```fish
$ for hash in (hashsort --list)
      echo === $hash ===
      hashsort --hash $hash fruit | head -n 2
      echo
  end

=== blake2b ===
Mango
Kiwi

=== blake2s ===
Fig
Elderberry
...
```

Pretty cool. :smile:

If you'd like to see the full source, it's part of my [dotfiles](https://github.com/jpverkamp/dotfiles) on GitHub: [hashsort](https://github.com/jpverkamp/dotfiles/blob/master/bin/hashsort)
