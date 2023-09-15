---
title: "AoC 2018 Day 12: Fat Cellular Automaton"
date: 2018-12-12
programming/languages:
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [Subterranean Sustainability](https://adventofcode.com/2018/day/12)

> **Part 1:** Create an infinite 2D [[wiki:cellular automaton]]() with transition rules based on two points to each side, starting with initial state at index 0 to the right.

> After 20 generations, what is the sum of indexes of points turned on?

<!--more-->

Okay. We have an unbounded cellular automaton with only two states (on/off), so we want to use a set of 'on' points. Let's load that:

```racket
; Read the initial state from the first line of stdin
(define INITIAL-STATE
  (for/set ([i (in-naturals)]
            [c (in-string (list-ref (string-split (read-line)) 2))]
            #:when (char=? c #\#))
    i))

(define _ (read-line))

; Read the rules from stdin, one per line, until we get them all
(define RULES
  (for/hash ([line (in-lines)])
    (define parts (string-split line))
    (values (list-ref parts 0) (string-ref (list-ref parts 2) 0))))
```

Next, we'll want a function to get the 5 characters around any given point so we can look things up in `RULES` and then a function that will do that for every value in the current state:

```racket
; Get the context of a point (2 on each side), used to look up RULES
(define (context state x)
  (list->string
   (for/list ([i (in-range (- x 2) (+ x 3))])
     (if (set-member? state i) #\# #\.))))

; Find the current minimum and maximum value
(define (bounds state)
 (values (apply min (set->list state))
         (apply max (set->list state))))

; Update the state by applying the RULES to each context
(define (update state)
  (define-values (lo hi) (bounds state))
  (for/set ([i (in-range (- lo 2) (+ hi 3))]
            #:when (char=? (hash-ref RULES (context state i) #\.) #\#))
    i))
```

With that, we can run the simulation as long as we want:

```racket
; Loop to calculate final state
(define FINAL-STATE
  (for/fold ([state INITIAL-STATE])
            ([generation (in-range (+ (generations) 1))])
    (update state)))

(printf "Final state: ~a plants, sum_index = ~a : ~a\n"
        (count-plants FINAL-STATE)
        (sum-plant-indexes FINAL-STATE)
        (string-trim (state->string FINAL-STATE) #px"\\.*"))
```

20 generations (with debug code turned on):

```racket
$ cat input.txt | racket fat-cellular-automaton.rkt --generations 20 --debug

gen 0, 53 plants, sum_index = 2356 : #.#..#..###.###.#..###.#####...########.#...#####...##.#....#.####.#.#..#..#.#..###...#..#.#....##
gen 1, 52 plants, sum_index = 2479 : ##..#####.##..###.##.##..#..##...#.....##.#...#..##....#.#..###.#.##...######..##.###.#####..#.....#
gen 2, 52 plants, sum_index = 2571 : ##.#..#.#.##.##.#..#.#####..#.###......#.#.####..#..##..##.###.##.#...#...###....##..#..#####...###
gen 3, 55 plants, sum_index = 2756 : #.###..##..#.#.####.#..#####.###....##..#.#.######..##....##.#.#.#.###...###.....#####.#..##...###
gen 4, 47 plants, sum_index = 2223 : ###.####..###..#.#.##.##.#..#..###.....###..#.#...###..#.....#.....#.###...###.....#..##.##..#...###
gen 5, 59 plants, sum_index = 3033 : ##..#.###.#####..##..#.#.#####.###.....#####..#...######...###...###.###...###...####...#.####...###
gen 6, 51 plants, sum_index = 2753 : ####.##..#..###..###..#.#..#..###.....#..#####...#...##...###...##..###...###...#.##.###.#.##...###
gen 7, 60 plants, sum_index = 3134 : #.#.#.#####.####.#####..#####.###...####.#..##.###....#...###....##.###...###.####...###.##.#...###
gen 8, 46 plants, sum_index = 2591 : ##....#.#..#..#.#..#..###.#..#..###...#.##.##....###..###...###.......###...##..#.##...##.#.#.#...###
gen 9, 55 plants, sum_index = 2757 : #..##..######..#####.###.#####.###.####..#.#....####.###...###.......###....#####.#....#.....#...###
gen 10, 48 plants, sum_index = 2653 : ####..##.#...###.#..#..##..#..#..##..#.####..#....#.#..###...###.......###....#..##.#..###...###...###
gen 11, 61 plants, sum_index = 3384 : #.###..#.#...###.#####..########..####.#.#####..##..##.###...###.......###..####..#.##.###...###...###
gen 12, 55 plants, sum_index = 3160 : ###.#####..#...##..#..###.#.....###.#.##.#.#..###..##....###...###.......####.#.######...###...###...###
gen 13, 52 plants, sum_index = 2920 : ##..#..#####....#####.###.#.....###.##.#...##.####..#....###...###.......#.##.#.#...##...###...###...###
gen 14, 47 plants, sum_index = 2782 : #####.#..##....#..#..###.#.....##.#.#.#......#.#####....###...###.....####.#...#....#...###...###...###
gen 15, 50 plants, sum_index = 3071 : #..##.##..#..#######.###.#......#.....#....###.#..##....###...###.....#.##.#.###..###...###...###...###
gen 16, 56 plants, sum_index = 3472 : ####...#.#####.#....#..###.#....###...###....###.##..#....###...###...####.#.#.####.###...###...###...###
gen 17, 55 plants, sum_index = 3312 : #.##.###.#..##.#..####.###.#....###...###....##.#.####....###...###...#.##...#.#.#..###...###...###...###
gen 18, 56 plants, sum_index = 3462 : ####...###.##..#.##.#.#..###.#....###...###.....#.#.#.##....###...###.####.#.##....##.###...###...###...###
gen 19, 52 plants, sum_index = 3183 : #.##...##.#.#####.#...##.###.#....###...###...##....##.#....###...##..#.##.##.#.......###...###...###...###
gen 20, 47 plants, sum_index = 2995 : ####.#....#.#.#..##.#......###.#....###...###....#.....#.#....###....#####..#.#.#.......###...###...###...###
Final state: 47 plants, sum_index = 3035 : #.##.#..##....##..#.#......###.#....###...###..###...##..#....###....#..####....#.......###...###...###...###
```

That's a pretty neat program. I wonder what part 2 will be...

> **Part 2:** What is the sum of indexes after 50 billion generations?

Okay. We could brute force that, but it might take a while...[^a while] So let's see what kind of input we're dealing with and see if we have a pattern:

```fish
$ for i in (seq 100 110)
      cat input.txt | racket fat-cellular-automaton.rkt --generations $i
  end

Final state: 75 plants, sum_index = 8019 : #.##.#.##.#.####.#..##.###.####.###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 72 plants, sum_index = 7883 : ####.#.##.#.#.#.##.##....##..#.#..###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 69 plants, sum_index = 7861 : #.##.##.#.....##..#.#.....###..##.###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 69 plants, sum_index = 7889 : ####..#.#.#......###..#.....####....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 69 plants, sum_index = 7964 : #.####....#......######.....#.##....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 71 plants, sum_index = 8097 : ###.#.##..###......#...##...####.#....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 72 plants, sum_index = 8186 : ###.##.##.###....###....#...#.##.#....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 73 plants, sum_index = 8367 : ##.#..#...###....###..###.####.#.#....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 72 plants, sum_index = 8357 : #.####...###....####.##..#.##...#....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 75 plants, sum_index = 8589 : ###.#.##...###....#.#.#.#####.#.###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 73 plants, sum_index = 8545 : ###.##.#...###..##....#.#..##.#.###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
```

Hmm.

```fish
$ for i in (seq 300 310)
      cat input.txt | racket fat-cellular-automaton.rkt --generations $i
  end

Final state: 73 plants, sum_index = 22350 : ###.#....###...###....###......###....###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 73 plants, sum_index = 22423 : ###.#....###...###....###......###....###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 73 plants, sum_index = 22496 : ###.#....###...###....###......###....###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 73 plants, sum_index = 22569 : ###.#....###...###....###......###....###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 73 plants, sum_index = 22642 : ###.#....###...###....###......###....###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 73 plants, sum_index = 22715 : ###.#....###...###....###......###....###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 73 plants, sum_index = 22788 : ###.#....###...###....###......###....###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 73 plants, sum_index = 22861 : ###.#....###...###....###......###....###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 73 plants, sum_index = 22934 : ###.#....###...###....###......###....###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 73 plants, sum_index = 23007 : ###.#....###...###....###......###....###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
Final state: 73 plants, sum_index = 23080 : ###.#....###...###....###......###....###....###....###....###.......###....###......###...###........###......###...........###......###....###...###...###.......###...###...###...###
```

That... that is interesting. At some point they've stabalized. It doesn't look like they're moving since I always display only the 'on' points. But what's actually happening is everything is moving to the right one index per generation and the pattern is 73 wide, resulting in 73 per generation. Always. So we can extrapolate:

```fish
$ math "(50000000000-300)*73+22277"

3650000000377
```

Which turns out to be the proper answer.

Much faster than waiting almost two centuries...[^cheaper]

[^a while]: 10k in 2.83 sec, 20k in 5.39 sec. So about 250 µs/generation. That's about 148 *days*. Let's not do that...
[^cheaper]: And cheaper than renting out a super computer...
