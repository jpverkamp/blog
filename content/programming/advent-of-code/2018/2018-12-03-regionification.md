---
title: "AoC 2018 Day 3: Regionification"
date: 2018-12-03
programming/languages:
- Python
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [No Matter How You Slice It](https://adventofcode.com/2018/day/3)

> **Part 1:** Given a list of overlapping regions defined by (left, top, width, height) count how many integer points occur in more than one region.

<!--more-->

Okay. First things first, we want to lay some groundwork. Let's create a structure in each language to store regions and functionality to load them.

First, Racket:

```racket
(provide (struct-out region)
         read-regions)

(struct region (id left top width height) #:transparent)

(define (read-region [in (current-input-port)])
  (define line (read-line in))
  (cond
    [(eof-object? line) line]
    [else
     (apply region
            (map string->number
                 (rest (regexp-match #px"#(\\d+) @ (\\d+),(\\d+): (\\d+)x(\\d+)"
                                     line))))]))

(define (read-regions [in (current-input-port)])
  (port->list read-region in))
```

I like how Racket structures input with a series of {{< doc racket read >}} functions. In this case, we'll use {{< wikipedia "regular expressions" >}} to read in the lines since they all have the same form.

The Python code looks much the same:

```python
RE_REGION = re.compile(r'#(\d+) @ (\d+),(\d+): (\d+)x(\d+)')

Region = collections.namedtuple(
    'Region',
    ['id', 'left', 'top', 'width', 'height'],
)

all_regions = []
for line in fileinput.input():
    id, left, top, width, height = RE_REGION.match(line).groups()
    all_regions.append(Region(
        int(id),
        int(left),
        int(top),
        int(width),
        int(height),
    ))
```

We can use {{< doc python "collections.namedtuple" >}} to make a cheap class and then the same regular expressions as last time to parse them.

Okay. Now that's out of the way, we want to tackle the actual problem. The simplest way in my mind to attack it is directly: loop over each region, then each point in that region, and add to a shared data structure for the region. By the time we're done, we have a dictionary of points to overlapping region counts:

```racket
(define regions-per-point
  (for*/fold ([count (hash)])
             ([r (in-list (read-regions))]
              [x (in-range (region-left r) (+ (region-left r) (region-width r)))]
              [y (in-range (region-top r) (+ (region-top r) (region-height r)))])
    (hash-update count (list x y) add1 0)))

(length
 (filter (λ (v) (> v 1))
         (hash-values regions-per-point)))
```

One thing I'm missing is the ability to unpack a region (a la {{< doc racket "match-define" >}}) within a `for` body. It would be cleaner than having to use all of the accessor functions. Sometimes I miss simple object notation.

In Python, the code has the same structure, but we have the notation I'm looking for:

```python3
counts = collections.defaultdict(lambda : 0)

for region in all_regions:
    for x in range(region.left, region.left + region.width):
        for y in range(region.top, region.top + region.height):
            counts[x, y] += 1

overlapping = 0

for x, y in counts:
    if counts[x, y] > 1:
        overlapping += 1

print(overlapping)
```

It looks like `counts` is indexed by two values, but that's actually a trick of the syntax. `x, y` is making a {{< doc python tuple >}}, the same as `(x, y)`. So the dictionary keys are tuples and the values are counts. {{< doc python "collections.defaultdict" >}} lets me update the counter without having to check for the first value.

And that's it:

```bash
$ cat input.txt | racket regionification.rkt

115304

$ cat input.txt | racket regionification.py

115304
```

> **Part 2:** There is one region in the input that does not overlap any other region. Find it.

Okay. We can't really re-use the functional part of part 1, but the structure to load regions works exactly the same. All we need is a function to detect if two regions overlap:

```racket
(define (overlaps? r1 r2)
  (match-define (region id1 left1 top1 width1 height1) r1)
  (match-define (region id2 left2 top2 width2 height2) r2)

  (not (or (<= (+ left1 width1) left2)
           (<= (+ left2 width2) left1)
           (<= (+ top1 height1) top2)
           (<= (+ top2 height2) top1))))
```

The idea is not to check if a given point from one region is in another, but rather the other way around: check if one region is entirely to the left of another or entirely above another. If either case for either order matches, the regions do _not_ overlap, otherwise, negate it.

With this, we have a weird looking nest of `for/first` loops to write:

```racket
(define input-regions (read-regions))

(for*/first ([r1 (in-list input-regions)]
             #:unless (for/first ([r2 (in-list input-regions)]
                                  #:when (and (not (eq? r1 r2))
                                              (overlaps? r1 r2)))
                        r2))
  r1)
```

The outer loop is finding the `first` region that has no overlap. Since by problem input we're guaranteed to have exactly one, that's good enough for me. The inner loop takes that region and returns the first region that is not the same region but overlaps it. If that `first` region exists, keep looking in the outer loop (the `#:unless`). It could probably be written more cleanly. But it works.

Now, in Python, the first thing I'm going to do is actually add the `overlaps` function to the `Region` class ({{< wikipedia "monkey patching" >}}):

```python3
def overlaps(self, other):
    return not (
        self.left + self.width <= other.left
        or other.left + other.width <= self.left
        or self.top + self.height <= other.top
        or other.top + other.height <= self.top
    )
Region.overlaps = overlaps
```

That lets us write things like `r1.overlaps(r2)`. Something about this seems wonderful to me. Then we can write the same loop as before:

```python3
for r1 in all_regions:
    found_overlap = False

    for r2 in all_regions:
        if r1 == r2:
            continue

        if r1.overlaps(r2):
            found_overlap = True
            continue

    if not found_overlap:
        print(r1)
        exit(0)
```

And that's it. The output looks a bit different between the two since we're printing the region in each case, but they're close enough:

```bash
$ cat input.txt | racket loner-region.rkt

(region 275 336 615 28 21)

$ cat input.txt | python3 loner-region.py

Region(id=275, left=336, top=615, width=28, height=21)
```

Took a bit longer than days previous. But not the end of the world.

We'll have to see how the remaining 22 days go...
