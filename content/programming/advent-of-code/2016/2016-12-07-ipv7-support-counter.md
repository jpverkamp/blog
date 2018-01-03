---
title: "AoC 2016 Day 7: IPv7 Support Counter"
date: 2016-12-07
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2016
---
### Source: [Internet Protocol Version 7](http://adventofcode.com/2016/day/7)

> **Part 1:** The input is a list of strings, potentially containing sequences in square brackets. Find all strings that have an ABBA sequence (two characters followed by the same two in reverse order) outside of any square brackets, but no ABBA sequences in square brackets.

<!--more-->

[![I know regular expressions](https://imgs.xkcd.com/comics/regular_expressions.png)](https://xkcd.com/208/)

```python
re_abba = re.compile(r'([a-z])((?!\1)[a-z])\2\1')

tls_valid = 0

with open(args.input, 'r') as fin:
    for line in fin:
        line = line.strip('\n')

        hypernet_list = []
        def store_and_replace(m):
            hypernet_list.append(m.group(0))
            return '--'

        supernet = re.sub(r'\[[a-z]+\]', store_and_replace, line)
        hypernet = '--'.join(hypernet_list)

        tls = ssl = False

        if re_abba.search(supernet) and not re_abba.search(hypernet):
            tls_valid += 1

print(tls_valid)
```

What I'm doing is first extracting characters in square brackets into a list (`hypernet_list`), replacing them with a string that won't match an ABBA pattern: `--`. Then I combine that list into a similar looking string. Then I apply the ABBA regex to both, checking for my condition. Let's look at that regex though:

```text
([a-z])((?!\1)[a-z])\2\1
```

To break that down, we have three parts:

```text
([a-z])       # First, match any character
((?!\1)[a-z]) # Then, match any character, but not the same one as the first group
\2\1          # Match the first two characters again in reverse order
```

The interesting part is the [negative lookhead](https://www.regular-expressions.info/lookaround.html) in the second group. It says, no matter what you match, it can't be this (this in this case being the first group `\1`). A bit complicated, but to my eyes at least, exactly the right tool for the job.

> **Part 2:** Count strings that have an ABA sequence outside of a bracketed section and a matching BAB section inside.

Finding ABA sequences isn't much harder, but you have to make sure that they can overlap (`re.findall(..., overlapped = True)`):

```python
re_aba = re.compile(r'([a-z])((?!\1)[a-z])\1')

ssl_valid = 0

with open(args.input, 'r') as fin:
    for line in fin:
        # ...

        ssl = False

        for (a, b) in re_aba.findall(supernet, overlapped = True):
            if b + a + b in hypernet:
                ssl = True

        if ssl: ssl_valid += 1

print(ssl_valid)
```

An interesting problem.
