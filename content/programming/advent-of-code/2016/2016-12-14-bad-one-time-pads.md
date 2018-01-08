---
title: "AoC 2016 Day 14: Bad One Time Pads"
date: 2016-12-14
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Hashes
series:
- Advent of Code 2016
---
### Source: [One-Time Pad](http://adventofcode.com/2016/day/14)

> **Part 1:** Calculate a series of MD5 hashes (the same as [Day 5]({{< ref "2016-12-05-password-cracker.md" >}})). A hash is considered valid if it contains a triple (three characters in a row) and somewhere in the next 1000 hashes there is a quintuple of that same character.

> What index produces the 64th key?

<!--more-->

We'll use the same hash function as last time, but this time, we will {{< wikipedia memoize >}} the results with {{< doc python "functools.lru_cache" >}}. This means that when we generate the next 1000 hashes ahead of time looking for quintuples, we don't have to redo the hashes again later. Hashes are pretty quick already, but this still has significant performance gains.

```python
@functools.lru_cache(None)
def hash(n):
    value = '{}{}'.format(args.salt, n)
    return hashlib.md5(value.encode()).hexdigest()
```

After that, we're just looking for 64 keys:

```python
keys = set()

for i in naturals():
    key = hash(i)

    for triple in re.findall(r'(.)\1\1', key):
        quintuple = triple * 5

        for j in range(i + 1, i + 1001):
            if quintuple in hash(j, args.stretch):
                keys.add(key)
                break

    if len(keys) >= args.count:
        break

print('{} keys generated after {} hashes'.format(len(keys), i))
```

To test the timing, we'll remove the cache:

```bash
$ # With cache
$ time python3 bad-one-time-pads.py --salt cuanljph --count 64

64 keys generated after 23769 hashes
        1.40 real         1.20 user         0.04 sys

$ # Without cache
$ time python3 bad-one-time-pads.py --salt cuanljph --count 64

64 keys generated after 23769 hashes
       12.16 real        10.40 user         0.26 sys
```


> **Part 2:** Implement {{< wikipedia "key stretching" >}}. Repeat the MD5 hash 2017 times.

Mostly, we need to update the hash function and pass in the new parameter:

```python
@functools.lru_cache(None)
def hash(n, repeat = 1):
    value = '{}{}'.format(args.salt, n)
    for i in range(repeat):
        value = hashlib.md5(value.encode()).hexdigest()
    return value

for i in naturals():
    key = hash(i, args.stretch)
    ...
```

Nothing else changes. The caching really helps this time:

```bash
$ # With cache
$ time python3 bad-one-time-pads.py --salt cuanljph --count 64 --stretch 2017

64 keys generated after 20606 hashes
       76.37 real        65.86 user         1.61 sys

$ # Without cache
$ time python3 bad-one-time-pads.py --salt cuanljph --count 64 --stretch 2017

64 keys generated after 20606 hashes
     6128.07 real      6016.67 user        20.45 sys
```

Ouch.
