---
title: "AoC 2016 Day 19: Blist Table"
date: 2016-12-19
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2016
---
### Source: [An Elephant Named Joseph](http://adventofcode.com/2016/day/19)

> **Part 1:** Create a [[wiki:circular list]]() of the numbers `1` through `n`. Going around the list, each currently remaining number removes the number after it. What is the last remaining number?

<!--more-->

I had a bit of fun with this solution, since I solved it with an infinite lazy list.

```python
def last_elf_standing(size):
    sad_elves = set()

    # The magic of lazy evaluation...
    elves = filter(lambda e : e not in sad_elves, itertools.cycle(range(1, size + 1)))

    while True:
        happy_elf = next(elves)
        sad_elf = next(elves)
        sad_elves.add(sad_elf)

        # A single elf is happy because they have lots of presents
        # But sad since they have no friends
        if happy_elf == sad_elf:
            return happy_elf

        logging.info('{} took presents from {}, {} elves remain'.format(
            happy_elf,
            sad_elf,
            size - len(sad_elves),
        ))

print('Last elf standing (sitting?): {}'.format(last_elf_standing(args.size)))
```

The basic idea is that we take the list of elves (`range(1, size + 1)`), make it infinitely repeating ({{< doc python "itertools.cycle" >}}), and filter out elves we've removed ({{< doc python filter >}}). Once we've removed enough that two adjacent elements are the same, we have the last remaining element. It's fast too.

> **Part 2:** Rather than removing the number immediately after the current number, remove the one half way around the board (breaking ties by rounding down).

Despite being quite simple to describe, this one is actually quite a bit more difficult. My first solution was to create a `Table` class that could remove arbitrary elements and use that:

```python
class Table(object):
    def __init__(self, size, function):
        self._index = 0
        self._size = size
        self._elves = list(range(1, size + 1))
        self._function = function

    def remove_one(self):
        if len(self._elves) <= 1:
            raise Exception('Last elf standing')

        happy_elf = self._elves[self._index]

        to_remove = eval(self._function, globals(), {
            'index': self._index,
            'size': self._size,
            'count': len(self._elves),
        })
        to_remove %= len(self._elves)
        sad_elf = self._elves[to_remove]

        self._elves.pop(to_remove)
        self._index += 1
        if self._index > len(self._elves):
            self._index = 0

    def last_elf_standing(self):
        while len(self._elves) > 1:
            self.remove_one()
        return self._elves[0]

table = Table(args.size, args.function)
last_elf = table.last_elf_standing()
print('Last elf standing (sitting?): {}'.format(last_elf))
```

Although this does work, the problem with it is that it's **very** slow. This is because Python lists are implemented under the hood as an array of contiguous values in memory. When you remove an element from the middle of the list, you have to copy everything that was after it down a spot. Arbitrarily doing that a few million times takes a while.

The solution was sound. We just needed a better data structure. Enter: [https://pypi.python.org/pypi/blist/](blist). Essentially, it's a list implemented under the hood as a [[wiki:binary tree]](). This gives you `O(log n)` removal, so that rather than taking over a million cycles on average (at the start), it takes {{< inline-latex "log(1,000,000) \equiv 14" >}}.

```python
def last_elf_standing(size, function = None):
    index = 0
    elves = blist.blist(range(1, size + 1))

    while len(elves) > 1:
        happy_elf = elves[index]

        if function:
            sad_elf_index = eval(args.function, globals(), {
                'index': index,
                'size': size,
                'count': len(elves),
            })
        else:
            sad_elf_index = index + 1

        sad_elf_index %= len(elves)

        sad_elf = elves[sad_elf_index]
        del elves[sad_elf_index]

        # If we removed an elf before us, the index doesn't change (the elf at that index does)
        if sad_elf_index >= index:
            index += 1
        index %= len(elves)

    return elves[0]

last_elf = last_elf_standing(args.size, args.function)
print('Last elf standing (sitting?): {}'.format(last_elf))
```

Much faster. It only takes a few seconds on my machine to crank through removing over 3 million elements from a list in semi-random ordering.

The comment there about not changing the index if we removed an elf earlier in the list took a little while to debug. It doesn't happen in the example they gave (too small). It wasn't until I stepped through a larger example on paper that I figured out what was going on there. 
