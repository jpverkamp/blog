---
title: "AoC 2016 Day 5: Password Cracker"
date: 2016-12-05
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Hashes
series:
- Advent of Code 2016
---
### Source: [How About a Nice Game of Chess?](http://adventofcode.com/2016/day/5)

> **Part 1:** Generate a series of hashes: MD5(salt + index). For each hash starting with five zeros, write down the sixth character.

<!--more-->

First, a helper function to generate an infinite list of natural numbers:

```python
def naturals(i = 0):
    while True:
        yield i
        i += 1
```

I have since learned that this function already exists in the standard library: {{< doc python "itertools.count" >}}. So it goes.

Then a second helper that will take a string and return its MD5 hash (in hex format):

```python
def md5(str):
    return hashlib.md5(str.encode()).hexdigest()
```

Then we just have to keep going until we have enough of a password:

```python
password = ''

for i in naturals():
    hash = md5(args.salt + str(i))

    if hash[:5] == '00000':
        password += hash[5]

    if len(password) == 8:
        break

print(password)
```

> **Part 2:** The sixth character now represents the position (0-7) in the password to write (only use the first write to each position; ignore 8-F as the sixth character). The seventh is the actual password character.

This one is somewhat more interesting. You have to:

- Determine where the new character would go and if that spot is available
- Determine what the new character would be
- Figure out when we've found all 8 characters

```python
hard_password = ['-'] * 8

for i in naturals():
    hash = md5(args.salt + str(i))

    if hash[:5] == '00000':
        index = hash[5]
        if index not in '01234567':
            continue

        index = int(index)
        if hard_password[index] != '-':
            continue

        hard_password[index] = hash[6]

    if not(any(c == '-' for c in hard_password)):
        break

print(hard_password)
```

I like Python's {{< doc python any >}} function. It reminds me of more {{< wikipedia "functional programming" >}} paradigms.

On fun thing you can do with the [full source](https://github.com/jpverkamp/advent-of-code/blob/master/2016/day-05/password-cracker.py) for today's solution is watch the progress as it cracks the password:

{{< figure src="/embeds/2016/password-cracker.gif" >}}

Skipping (many) frames to keep the file size reasonable. Created with [asciinema](https://asciinema.org/), [asciicast2gif](https://github.com/asciinema/asciicast2gif), and [gifsicle](https://www.lcdf.org/gifsicle/)... That should be easier.
