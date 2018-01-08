---
title: "AoC 2017 Day 4: Password Validator"
date: 2017-12-04
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Regular Expressions
series:
- Advent of Code 2017
---
### Source: [High-Entropy Passphrases](http://adventofcode.com/2017/day/4)

> **Part 1:** Given a list of {{< wikipedia passphrases >}}, count how many contain no duplicate words.

<!--more-->

There are two ways that I worked out how to solve this problem. First, you can use {{< wikipedia "regular expressions" >}} with the `\b` 'word boundary' marker:

```python
valid_count = 0

for line in lib.input():
    if not re.search(r'\b(\w+)\b.*?\b\1\b'):
        valid_count += 1

print(valid_count)
```

This means:

- `\b(\w+)\b` - match any complete word (`\b` matches only boundaries between non-word characters (like spaces and the start/end of a string) and word-characters)
- `.*` - match anything between the two words
- `\b\1\b` - match the first group above, but only if it's a complete word (this avoids matching `aa aaa`)

Alternatively, you can use a {{< doc python set >}} to compare the words. If the number of words in the list and the set are different, there was at least one duplicate:

```python
valid_count = 0

for line in lib.input():
    words = line.split()

    if len(words) == len(set(words)):
        valid_count += 1

print(valid_count)
```

> **Part 2:** Passphrases may no longer contain {{< wikipedia anagrams >}}. How many are still valid?

This would be rather more difficult to solve with regular expressions[^alice], but it's actually pretty straight forward with the `set` based solution:

```python
valid_count = 0

for line in lib.input():
    words = [''.join(sorted(word)) for word in line.split()]

    if len(words) == len(set(words)):
        valid_count += 1

print(valid_count)
```

Rather than trying to scramble all of the words to find anagrams, we replace each word with the letters in lexicographic order. That means that any anagrams will become the same word. We can then use the same `len(words) == len(set(words))` code as before to look for duplicates.

Run it to check timing:

```bash
$ python3 run-all.py day-04

day-04  python3 password-validator.py input.txt 0.062463998794555664    337
day-04  python3 password-validator.py input.txt --no-anagrams   0.06604528427124023     231
```

[^alice]: Is this even possible? Since the words can be arbitrarily long, I'm not certain that it is.
