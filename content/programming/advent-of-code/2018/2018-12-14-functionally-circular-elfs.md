---
title: "AoC 2018 Day 14: Functionally Circular Elfs"
date: 2018-12-14
programming/languages:
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [Chocolate Charts](https://adventofcode.com/2018/day/14)

> **Part 1:** Create an infinite stream of numbers, by starting with [3, 7] with two pointers: 0 and 1. To add values to the list:

> - Add the current values of the two pointers
>   - If the value is less than ten, add that value to the end of the list
>   - If the value is greater or equal to ten, add 1 and then the ones digits to the end of the list
> - Update each pointer by adding the value it is pointing at to its current index plus one

> With that algorithm, find the ten digits after a given index.

<!--more-->

Fascinating.

My first inclination is that I want circular lists. But the code I have from [Marble Madness]({{< ref "2018-12-09-marble-madness.md" >}}) won't quite work, since I also need to keep track of the two pointers.

My second inclination is that I want an array of values where I can cheaply add values to the end and index arbitrary elements. What I really want is something like an {{< doc java ArrayList >}} from Java. But this is Racket. Let's just fake it with a {{< doc racket hash >}} keyed on integers and a length. Not quite as memory efficient, but it will work.

```racket
(struct state (data length elf1 elf2) #:transparent)

(define (initial-state)
  (state (hash 0 3 1 7)
         2
         0
         1))
```

Now, we can start building up increasingly complicated functions. First, we want a function that can add a single value to the end of the list. Second, add either one or two values based on the current pointers (if the sum is greater than 10 or not). Third, move the pointers based on their current values:

```racket
; Add a single value to the end of the current state
(define (add-recipe s v)
  (match-define (state data length elf1 elf2) s)
  (state (hash-set data length v)
         (add1 length)
         elf1
         elf2))

; Add one or two recipes to the state
(define (add-recipes s)
  (match-define (state data length elf1 elf2) s)
  (define sum (+ (hash-ref data elf1) (hash-ref data elf2)))
  (cond
    [(>= sum 10)
     (add-recipe (add-recipe s (quotient sum 10)) (remainder sum 10))]
    [else
     (add-recipe s sum)]))

; Update each elf's current recipe
; Wrap values that run off the end of the current list back to the beginning
(define (move-elfs s)
  (match-define (state data length elf1 elf2) s)
  (state data
         length
         (remainder (+ elf1 (hash-ref data elf1) 1) length)
         (remainder (+ elf2 (hash-ref data elf2) 1) length)))
```

And with that, we can expand the current list:

```racket
; Do a full update
(define (tick s)
  (move-elfs (add-recipes s)))
```

I always love when the final version of a function is next to nothing because of the work you've already put in.

So, how do we find the 10 values after a given point? Well, first we have to make the list long enough, then just pull them out of `state-data`:

```racket
; Calculate the score after a coordinate
(define (score i)
  (define state
    (let loop ([s (initial-state)])
      (cond
        [(< (state-length s) (+ i 10))
         (loop (tick s))]
        [else s])))
  (for/list ([i (in-range i (+ i 10))])
    (hash-ref (state-data state) i)))
```

With a quick helper to turn that into a single number:

```racket
(define (digits->int ls)
  (let loop ([n 0] [digits ls])
    (cond
      [(null? digits) n]
      [else
       (loop (+ (* n 10) (first digits))
             (rest digits))])))

(define argv (current-command-line-arguments))
(for ([arg (in-vector argv)])
  (printf "input: ~a\n" arg)
  (printf "[part1] ~a\n" (digits->int (score (string->number arg)))))
```

And for my input:

```bash
$ racket functionally-circular-elfs.rkt 157901

input: 157901
[part1] 9411137133
```

Nice.

> **Part 2:** Given a sequence of digits, what is the index of the first occurance of those digits?

This is computationally a bit more interesting. It actually reminds me of [a post I wrote all the way back in 2012]({{< ref "2012-09-16-a-needle-in-a-pi-stack.md" >}})...

The goal here will be to keep a list of digits we have left to find and scan through the current list of numbers, expanding it whenever we need more. If we get a partial match but then an error, just reset to the original list of digits:

```racket
; Find a specific pattern in the input stream
(define (search ls)
  (let loop ([state (initial-state)]
             [index 0]
             [to-find ls])
    (when (zero? (remainder index 1000)) (displayln index))
    (cond
      ; Found our target, return the index it started at
      [(null? to-find) (- index (length ls))]
      ; Don't have enough data, generate some more
      [(>= index (state-length state))
       (loop (tick state) index to-find)]
      ; The current match continues
      [(equal? (first to-find) (hash-ref (state-data state) index))
       (loop state (add1 index) (rest to-find))]
      ; The current match does not continue, reset to where we started + 1
      [else
       (loop state (+ (- index (length ls)) (length to-find) 1) ls)])))
```

For full output:

```racket
(define (int->digits n)
  (let loop ([n n] [digits '()])
    (cond
      [(< n 10) (list* n digits)]
      [else (loop (quotient n 10)
                  (list* (remainder n 10) digits))])))

; Find score/search for any given values
(define argv (current-command-line-arguments))
(for ([arg (in-vector argv)])
  (printf "input: ~a\n" arg)
  (printf "[part1] ~a\n" (digits->int (score (string->number arg))))
  (printf "[part2] ~a\n" (search (int->digits (string->number arg)))))
```

```bash
$ racket functionally-circular-elfs.rkt 157901

input: 157901
[part1] 9411137133
[part2] 20317612
```

This is actually a really neat problem since my original approach was not at all functional, using mutation in order to create a proper doubly-linked list with pointers to the two elf nodes. But not only was it not as 'pure' it was actually a lot more complicated and ugly code. This is just so much nicer to work with. :smile:
