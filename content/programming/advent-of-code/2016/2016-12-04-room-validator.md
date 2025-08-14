---
title: "AoC 2016 Day 4: Room Validator"
date: 2016-12-04
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Regular Expressions
series:
- Advent of Code 2016
---
### Source: [Security Through Obscurity](http://adventofcode.com/2016/day/4)[^1]

> **Part 1:** A room is described as a name, a sector ID, and a checksum as follows:
> 
> ```
> aaaaa-bbb-z-y-x-123[abxyz]
> 
> name: aaaaa-bbb-z-y-x
> sector ID: 123
> checksum: abxyz
> ```
> 
> A room is valid if the checksum contains the five most common letters if the name (ties broken alphabetically).

<!--more-->

An interesting problem. The first thing that we have to do is parse the input:

```python
with open(args.input_file, 'r') as fin:
    for room in fin:
        m = re.match(r'([a-z-]+)-(\d+)\[([a-z]+)\]', room)
        name, sector_id, checksum = m.groups()

        ...
```

The next thing we want to do is generate a checksum (so we can see if it's correct):

```python
def generate_checksum(name):
    '''
    Custom checksum function by sorting all characters in the input on a tuple
    of: length (shortest first) and the letter itself for alphabetical sorting.
    '''

    return ''.join(list(sorted(
        set(name) - {'-'},
        key = lambda letter : (
            -name.count(letter),
            letter
        )
    )))[:5]
```

Specifically, we're going to create a list of letters in the string (removing dashes), then order them with a custom `key`: how many times they occur in the string. Negate this number so that we get the most first, and then put it in a tuple of `(-count, letter)` so that ties are broken by the letter. We couldn't just reverse the list since the count is sorted descending and the letters ascending.

Combined the two by checking if checksum is valid:

```python
valid_sector_id_sum = 0

with open(args.input_file, 'r') as fin:
    for room in fin:
        m = re.match(r'([a-z-]+)-(\d+)\[([a-z]+)\]', room)
        name, sector_id, checksum = m.groups()

        if checksum != generate_checksum(name):
            continue

        valid_sector_id_sum += int(sector_id)

print('sum of valid ids:', valid_sector_id_sum)
```

And we're good to go.

> **Part 2:** Decrypt the 'real name' of each room by applying a [[wiki:Caesar cipher]]() with the sector ID. Find the ID containing 'North Pole objects'.

What exactly a 'North Pole object' is isn't yet clear, but we can write the decryption function easily enough:

```python
def decrypt(name, key):
    '''Shift all characters in the name by key positions.'''

    offset = ord('a')
    def shift(c):
        if c == '-':
            return ' '
        else:
            return chr((ord(c) - offset + key) % 26 + offset)

    return ''.join(map(shift, name))
```

Since [[wiki:ASCII]]() characters don't start with `a = 0` or `a = 1` (but rather `a = 97`), we have to offset the characters by that much before applying the subtraction modulo 26. It works though:

```python
>>> decrypt('qzmt-zixmtkozy-ivhz', 343)
very encrypted name
```

Using that and assuming that any 'North Pole object' has the word north in the name, we can update our loop:

```python
potential_north_sectors = []

with open(args.input_file, 'r') as fin:
    for room in fin:
        m = re.match(r'([a-z-]+)-(\d+)\[([a-z]+)\]', room)
        name, sector_id, checksum = m.groups()

        if checksum != generate_checksum(name):
            continue

        real_name = decrypt(name, int(sector_id))
        if 'north' in real_name:
            potential_north_sectors.append((real_name, sector_id))

for real_name, sector_id in potential_north_sectors:
    print(real_name, '@', sector_id)
```

It only prints a single value (for my input), so that's good enough for me!

[^1]: Don't do this.
