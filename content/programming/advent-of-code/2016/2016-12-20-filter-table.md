---
title: "AoC 2016 Day 20: Filter Table"
date: 2016-12-20
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Data Structures
series:
- Advent of Code 2016
---
### Source: [Firewall Rules](http://adventofcode.com/2016/day/20)

> **Part 1:** Given a list of integer ranges (a la `5-8`), what is the first value not in any given range?

<!--more-->

Most of this problem actually came down to making a relatively complicated data structure that can take an arbitrary number of overlapping ranges and simplify them, also allowing the addition and removal of more ranges. It's more complicated than it strictly needs to be, but it makes this problem much easier. :)

```python
class IntRange(object):
    '''
    Represents a list of integers.

    Specific values can be allowed (included) / denied (excluded) from the range.
    '''

    def __init__(self, min, max):
        '''Create a new int range with the given values initially allowed.'''

        self._ranges = [(min, max)]

    def __repr__(self):
        '''Pretty print a range (this can get long).'''

        return 'IntRange<{}>'.format(self._ranges)

    def __in__(self, value):
        '''Test if a value is in this int range.'''

        # Slower version
        # return any(lo <= value <= hi for (lo, hi) in self._ranges)

        index = bisect.bisect(self._ranges, (value, value))
        lo, hi = self._ranges[index]
        return lo <= value <= hi

    def __iter__(self):
        '''Return all values in this int range.'''

        for (lo, hi) in self._ranges:
            yield from range(lo, hi + 1)

    def __len__(self):
        '''Return how many values are in this IP range.'''

        return sum(hi - lo + 1 for (lo, hi) in self._ranges)

    def _simplify(self):
        '''Go through current ranges and remove/collapse overlapping ranges.'''

        i = 0
        while i + 1 < len(self._ranges):
            range1_lo, range1_hi = self._ranges[i]
            range2_lo, range2_hi = self._ranges[i + 1]

            # Only guarantee: lo1 is <= lo2

            # There is an overlap, combine and remove range2
            # Continue without incrementing since another range might be collapsed
            if range2_lo <= range1_hi:
                self._ranges[i] = (range1_lo, max(range1_hi, range2_hi))
                del self._ranges[i + 1]
                continue

            i += 1

    def allow(self, allow_min, allow_max):
        '''Add a new range of allowed values.'''

        # Insert sorted (using bisect) then simplify
        bisect.insort(self._ranges, (allow_min, allow_max))
        self._simplify()

    def deny(self, deny_min, deny_max):
        '''Remove a range of (possibly) previously allowed values.'''

        i = 0
        while i < len(self._ranges):
            lo, hi = self._ranges[i]

            # Range is completely denied
            if deny_min <= lo <= hi <= deny_max:
                del self._ranges[i]
                continue

            # Denial is completely within the range, split it
            elif lo <= deny_min <= deny_max <= hi:
                del self._ranges[i]
                self._ranges.insert(i, (lo, deny_min - 1))
                self._ranges.insert(i + 1, (deny_max + 1, hi))

            # Partial overlap, adjust the range
            elif lo <= deny_min <= hi:
                self._ranges[i] = (lo, deny_min - 1)

            elif lo <= deny_max <= hi:
                self._ranges[i] = (deny_max + 1, hi)

            i += 1
```

The interesting functions there are:

- `allow` where I use the {{< doc python bisect >}} module to insert elements into a sorted position in a list
- `_simplify` where I take a sorted list and combine overlapping adjacent elements (as part of `allow`)
- `deny` where I iterate through the list and remove/combine existing ranges that have been deleted or broken apart

`deny` took the most time, but it was still relatively straight forward.

```python
lo, hi = map(int, args.range.split('-'))
ips = IntRange(lo, hi)

for line in fileinput.input(args.files):
    if line:
        lo, hi = map(int, line.split('-'))
        ips.deny(lo, hi)

for ip in ips:
    print('First allowed IP: {}'.format(ip))
    break
```

> **Part 2:** How many numbers are there between `0` and `2^32-1` (inclusive) are not in any range?

We already solved this with the `__len__` method of `IntRange`:

```python
print('Number of allowed IPs: {}'.format(len(ips)))
```

Interesting aside: You could probably do this with Python's built in {{< doc python ipaddress >}} module, specifically using a list of {{< doc python "ipaddress.IPv4Network" >}}. I thought it was interesting to work out myself though.
