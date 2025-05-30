---
title: Combining sort and uniq
date: 2014-02-07 00:05:00
programming/languages:
- Python
programming/topics:
- Dotfiles
- Open Source
- Unix
---
A fairly common set of command line tools (at least for me) is to combine `sort` and `uniq` to get a count of unique items in a list of unsorted data. Something like this:

```bash
$ find . -type 'f' | rev | cut -d "." -f "1" | rev | sort | uniq -c | sort -nr | head

2649 htm
1458 png
 993 cache
 612 jpg
 135 css
 102 zip
  99 svg
  60 gif
  45 js
  27 pdf
```

<!--more-->

To break that down a little bit:

```bash
find . -type 'f'
```

Returns a list of all `f`iles in the current directory (`.`).

```bash
rev | cut -d "." -f "1" | rev
```

Pulls of the extension by `rev`ersing the line, then cut off the first `.` `d`elimted field `f`ield (previously the last), and `rev`ersing it again.

```bash
sort
```

Sorts the lines so that `uniq` will work correctly.

```bash
uniq -c
```

Collapse adjacent equalivalent lines, outputing a `c`ount with each. This is why we had to `sort` first, otherwise something like `a b a a` would collapse to `a b a` rather than `a b`.

```bash
sort -nr
```

Sort again, this time taking into account that the first field is `n`umeric (the count from `uniq`) and `r`eversing the result so that the highest values are first.

```bash
head
```

Returning only the first `n` (default is 10) lines.

Running it on my blog directory, we see that it shows a whole pile of various kinds of files (the `cache` files are partially generated content unique to my blog generator).

But there's a bit of a problem with using `sort` and `uniq` together that way: they aren't aware of one another. So to sort the document, you have to hold the entire thing in memory. If you're running what I was above (~5k lines), that's not much. But if you try to do the same thing with several gigabytes of text...

Let's write a quick script that can do that all at once:

```python
parser = argparse.ArgumentParser()
parser.add_argument('-k', '--key-sort',   dest='keySort', action='store_true')
parser.add_argument('-v', '--value-sort', dest='valSort', action='store_true')
parser.add_argument('-r', '--reverse',    dest='reverse', action='store_true')
parser.add_argument('-n', '--numeric',    dest='numeric', action='store_true')

args = parser.parse_args()

if args.keySort and args.valSort:
    print('Cannot sort by both key and value')
    exit()

counts = collections.defaultdict(lambda : 0)
for line in sys.stdin:
    counts[line.strip()] += 1

f = int if args.numeric else lambda x : x

values = counts.items()
if args.keySort: values = sorted(values, key = lambda el: f(el[0]))
if args.valSort: values = sorted(values, key = lambda el: f(el[1]))
if args.reverse: values = reversed(values)

for k, v in values:
    print('{0}\t{1}'.format(v, k))
```

Even better, it combines several flags from both `uniq` and the second `sort`. You can sort by either the key or value (value being the count). You can reverse and you can do a numeric sort. So if you want to do the same thing as above:

```bash
$ find . -type 'f' | rev | cut -d "." -f "1" | rev | count -vnr | head

2649    htm
1458    png
993     cache
612     jpg
135     css
102     zip
99      svg
60      gif
45      js
27      pdf
```

Much shorter! Granted, if you really wanted to, you can do this just as easily with `awk`:

```bash
$ find . -type 'f' | \
  awk -F. '{ exts[$(NF)]++; } END { for (ext in exts) print exts[ext] "\t" ext }' | \
  sort -nr | head

2649    htm
1458    png
993     cache
612     jpg
135     css
102     zip
99      svg
60      gif
45      js
27      pdf
```

Basically, `awk` is splitting the string on the `F`ield `.`, then running this script on each line:

```awk
exts[$(NF)]++;
```

`NF` is the number of fields, so `$(NF)` refers to the last field. `exts[$(NF)]++` adds on to a dictionary keyed on the extension (`$(NF)`). Through the magic of default values, this works, defaulting any missing keys to 0 the first time around.

Then, after all of the lines are done, the `END` segment runs:

```awk
for (ext in exts) print exts[ext] "\t" ext
```

This loops over each extension, printing first the count then the extension.

The downsides? It's a lot longer (although you could alias it) and you have to manually sort. Still, it worth manually knowing some `awk`, especially for the cases where you're on a remote system and don't have custom dotfiles installed.

As before, this script is available in my [dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}}) repository: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/count">count</a>.
