---
title: "AoC 2018 Day 1: Sum-thing to start with"
date: 2018-12-01 00:00:03
programming/languages:
- Python
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [Chronal Calibration](https://adventofcode.com/2018/day/1)

> **Part 1:** Given a list of numbers (positive and negative) calculate the sum.

<!--more-->

First, in Racket. We have to take all the numbers in a file (which are {{< doc racket read >}}able, so you can do that with {{< doc racket "port->list" >}}, which `read`s an entire port into a `list`. Then just {{< doc racket apply >}} `+` to the whole shebang[^shebang]:

```racket
(apply + (port->list))
```

That really does work:

```bash
$ cat input.txt | racket summification.rkt

416
```

It's a bit more verbose in Python, but only barely:

```python3
sum = 0
for line in fileinput.input():
    sum += int(line.strip())

print(sum)
```

And this way we get to leverage the lovely {{< doc python fileinput >}} library, which means we can run it a couple different ways:

```bash
$ cat input.txt | python3 summification.py

416

$ python3 summification.py input.txt

416
```

{{< figure src="/embeds/2018/joliver-cool.gif" >}}


> **Part 2:** Assuming the same input loops forever, what is the first running sum that you see twice?

Since we aren't just reading the entire input once (it could be less than once if we see a duplicate quickly or many times, depending on the input[^proveit]), this isn't quite as easy to write up.

In Racket, what we want to do is first capture the `input` list, then set up a loop that will keep track of three things:

- The current input (which will reset when we run out)
- The current sum
- All sums we've seen before so we can detect duplicates

We can do all that with this:

```racket
(define input (port->list))

(let loop ([seq input]
           [sum 0]
           [seen (set)])
  (cond
    [(null? seq)
     (loop input sum seen)]
    [(set-member? seen (+ (first seq) sum))
     (+ (first seq) sum)]
    [else
     (define new-sum (+ (first seq) sum))
     (loop (rest seq) new-sum (set-add seen new-sum))]))
```

None too shabby.

In this case, the Python code can lean on a library that the Racket code cannot (as easily), using the {{< doc python itertools >}} library (specifically the `cycle` function) to automagically make a cycle of the input without us having to do anything[^racketcycle]!

```python
sum = 0
seen = set()

for line in itertools.cycle(fileinput.input()):
    sum += int(line.strip())
    if sum in seen:
        break
    seen.add(sum)

print(sum)
```

And--as hoped--we get the same input in both cases:

```bash
$ cat input.txt | racket duplification-detector.rkt

56752

$ cat input.txt | python3 duplification-detector.py

56752
```

1 done! 24 to go...

[^shebang]: It's funny because [[wiki:shebang (unix)]]().

[^proveit]: It's not actually guaranteed to even terminate. Consider the input that is just the number 1.

[^racketcycle]: Racket does have {{< doc racket in-cycle >}}, but I didn't quite get it to work cleanly with what we want here.
