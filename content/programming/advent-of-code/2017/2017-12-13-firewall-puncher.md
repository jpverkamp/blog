---
title: "AoC 2017 Day 13: Firewall Puncher"
date: 2017-12-13
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2017
---
### Source: [Packet Scanners](http://adventofcode.com/2017/day/13)

> **Part 1:** Multiple layers are defined with rules of the form:

> - {index}: {depth}

> Each layer will start at position 0, then once per tick will advance towards depth. Once it hits `depth-1`, it will return to position 0, taking `2*depth-1` per full cycle.

> Calculate the sum of `index * depth` for any scanners that are at position `0` when you pass through them given an initial starting time.

<!--more-->

The main simplifying assumption you can make is that you don't actually have to simulate all of the layers. You just have to calculate where it will be when you get there:

```python
def calculate_severity(delay):
    '''
    Calculate how severe the alarm is if you start at the given tick.
    '''

    total_severity = 0

    for depth in firewalls:
        range = firewalls[depth]

        cycle_length = (range - 1) * 2
        position = (delay + depth) % cycle_length

        # This isn't actually necessary, but makes debugging easier
        if position > range:
            position = 2 * range - position

        if position == 0:
            severity = depth * firewalls[depth]
            total_severity += severity

    return total_severity
```

You can use this to find the severity starting at a given ticket:

```python
tick = lib.param('tick')
severity = calculate_severity(tick)
print(f'{tick}: severity {severity}')
```

> **Part 2:** Find the first timestamp you can delay to such that you are never at position `0` with the scanner for any layer.

For this, we don't care about total severity so we can modify that function to bail out early:

```python
def calculate_severity(delay, return_pass_all = False):
    '''
    Calculate how severe the alarm is if you start at the given tick.

    If return_pass_all is set, return True if you hit no walls and False if you
    hit any (even if the severity would be 0).
    '''

    total_severity = 0

    for depth in firewalls:
        range = firewalls[depth]

        cycle_length = (range - 1) * 2
        position = (delay + depth) % cycle_length

        if position > range:
            position = 2 * range - position

        if position == 0:
            severity = depth * firewalls[depth]
            total_severity += severity

            if return_pass_all:
                return False

    if return_pass_all:
        return True
    else:
        return total_severity
```

Then just iterate until we find a safe tick:

```python
safe_tick = None
for tick in itertools.count():
    lib.log('=== {} ===', tick)
    if calculate_severity(tick, return_pass_all = True):
        safe_tick = tick
        break

print(f'safe: {safe_tick}')
```

It's slow, but less than a minute so it works out:

```bash
$ python3 run-all.py day-13

day-13  python3 firewall-puncher.py input.txt --tick 0  0.07503604888916016     0: severity 1476
day-13  python3 firewall-puncher.py input.txt --safest  23.190335035324097      safe: 3937334
```

If I wanted to optimize this, what we're looking for is the {{< wikipedia "least common multiple" >}} of all of the cycle lengths when offset by the depths. That seems like something that should be possible.
