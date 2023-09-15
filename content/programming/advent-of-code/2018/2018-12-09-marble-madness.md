---
title: "AoC 2018 Day 9: Marble Madness"
date: 2018-12-09
programming/languages:
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [Marble Mania](https://adventofcode.com/2018/day/9)

> **Part 1:** Place marbles in a circle such that each marble is placed by skipping one place *except* for marbles divisible by 23. For those, don't place them, skip back 7 places, and remove that marble as well. Add these two marbles to your current score.

> Given a specific player count and last marble, what's the highest score?

<!--more-->

Well. That's a thing. What this problem really comes down to is a custom data structure problem. What we want is a [[wiki:circular list]](), where you can spin the list forward or backwards and efficiently add/remove the item at the first element of the list.

Since Racket doesn't seem to have a data structure exactly like this, what I'm going to do is create my own by combining two lists. Essentially, we'll have a list of items before (`prev`) to the current `head` of the list (stored in reverse order) and another for items after (`next`) the current `head`. As we move forward, we move items from `next` to `prev` and backwards is the reverse. If either list runs out, you can refresh it by applying a `reverse` to its partner list. `reverse` is expensive, but you only rarely need to do it (depending on performance) leading to a decent [[wiki:text="amortized runtime" page="amortized analysis"]](). Fun times.

```racket
#lang racket

(provide (all-defined-out))

(struct circular-list (prev next)
  #:transparent
  #:methods gen:custom-write
  [(define write-proc
     (λ (cls out depth)
       (fprintf out "#<circular-list ~a>" (circular-list->list cls))))])

; Create an empty circular list
(define (make-circular-list)
  (circular-list '() '()))

; Turn a list into a circular list
(define (list->circular-list ls)
  (circular-list '() ls))

; Turn a circular list back into a regular one at the current point
(define (circular-list->list cls)
  (match-define (circular-list prev next) cls)
  (append next (reverse prev)))

; Test if a circular list contains no elements
(define (circular-list-empty? cls)
  (match-define (circular-list prev next) cls)
  (and (null? prev) (null? next)))

; Get size of a circular-list
(define (circular-list-length cls)
  (match-define (circular-list prev next) cls)
  (+ (length prev) (length next)))

; Look at the current first item of a circular list
(define (circular-list-peek cls)
  (match-define (circular-list prev next) cls)
  (cond
    [(null? next) (last prev)]
    [else (first next)]))

; Add a new item to the head of a circular list
(define (circular-list-push cls value)
  (match-define (circular-list prev next) cls)
  (circular-list (list* value prev) next))

; Remove the current head of a circular list
(define (circular-list-pop cls)
  (match-define (circular-list prev next) cls)
  (cond
    [(null? next)
     (define next (reverse prev))
     (circular-list '() (rest next))]
    [else
     (circular-list prev (rest next))]))

; Rotate a circular list n positions
; Positive numbers rotate 'forward', negative 'backwards'
(define (circular-list-rotate cls [steps 1])
  (match-define (circular-list prev next) cls)
  (let loop ([prev (circular-list-prev cls)]
             [next (circular-list-next cls)]
             [steps steps])
    (cond
      [(zero? steps) (circular-list prev next)]
      [(negative? steps)
       (cond
         [(null? prev)
          (define prev (reverse next))
          (loop (rest prev) (list (first prev)) (add1 steps))]
         [else
          (loop (rest prev) (list* (first prev) next) (add1 steps))])]
      [else
       (cond
         [(null? next)
          (define next (reverse prev))
          (loop (list (first next)) (rest next) (sub1 steps))]
         [else
          (loop (list* (first next) prev) (rest next) (sub1 steps))])])))

; Rotate a circular list until the head matches the given prediate
(define (circular-list-rotate-until cls pred?)
  (let loop ([length (circular-list-length cls)]
             [cls cls])
    (cond
      [(or (zero? length)
           (pred? (circular-list-peek cls)))
       cls]
      [else
       (loop (sub1 length)
             (circular-list-rotate cls -1))])))
```

That's a bit of code. `circular-list-rotate` is by far the most interesting code (since it has to handle reversing the lists), but hopefully still worth it.

Ironically, the code I had a bug in for the longest time? `circular-list-peek`. When all of the data was in `prev`, I was taking the `first` instead of `last` element... Oops. Works much better when you do it correctly.

With all that code, the solution is hopefully not nearly as complicated:

```racket
(let loop ([players (list->circular-list (range 1 (add1 (players))))]
           [scores (hash)]
           [table (list->circular-list '(0))]
           [marble 1])
  (cond
    ; Used up the last marble, output scores
    [(= marble (add1 (last-marble)))
     (apply max (hash-values scores))]
    ; Marbles divisible by 23 scores 23 + removes the marble 7 ago
    [(= 0 (remainder marble 23))
     (let* ([table (circular-list-rotate table -8)]
            [score (+ (circular-list-peek table) marble)]
            [table (circular-list-pop table)]
            [table (circular-list-rotate table 1)])
       (loop (circular-list-rotate players)
             (hash-update scores (circular-list-peek players) (curry + score) 0)
             table
             (add1 marble)))]
    ; All other marbles skip 1 and insert the marble
    [else
     (loop (circular-list-rotate players)
           scores
           (circular-list-push (circular-list-rotate table) marble)
           (add1 marble))]))
```

Well look at that.

```bash
$ racket marble-madness.rkt --players 477 --stop-at 70851

374690
```

I did create a print function that prints more or less the same thing in the problem statement to help debug:

```racket
(let loop ([players (list->circular-list (range 1 (add1 (players))))]
           [scores (hash)]
           [table (list->circular-list '(0))]
           [marble 1])

  (when (debug)
    (printf "[~a] [head:~a] ~a\n"
            (circular-list-peek players)
            (circular-list-peek (circular-list-rotate table))
            (circular-list-rotate-until table zero?)))

  ...)
```

Pretty handy:

```racket
$ racket marble-madness.rkt --players 9 --stop-at 26 --debug

[1] [head:0] #<circular-list (0)>
[2] [head:1] #<circular-list (0 1)>
[3] [head:0] #<circular-list (0 2 1)>
[4] [head:2] #<circular-list (0 2 1 3)>
[5] [head:1] #<circular-list (0 4 2 1 3)>
[6] [head:3] #<circular-list (0 4 2 5 1 3)>
[7] [head:0] #<circular-list (0 4 2 5 1 6 3)>
[8] [head:4] #<circular-list (0 4 2 5 1 6 3 7)>
[9] [head:2] #<circular-list (0 8 4 2 5 1 6 3 7)>
[1] [head:5] #<circular-list (0 8 4 9 2 5 1 6 3 7)>
[2] [head:1] #<circular-list (0 8 4 9 2 10 5 1 6 3 7)>
[3] [head:6] #<circular-list (0 8 4 9 2 10 5 11 1 6 3 7)>
[4] [head:3] #<circular-list (0 8 4 9 2 10 5 11 1 12 6 3 7)>
[5] [head:7] #<circular-list (0 8 4 9 2 10 5 11 1 12 6 13 3 7)>
[6] [head:0] #<circular-list (0 8 4 9 2 10 5 11 1 12 6 13 3 14 7)>
[7] [head:8] #<circular-list (0 8 4 9 2 10 5 11 1 12 6 13 3 14 7 15)>
[8] [head:4] #<circular-list (0 16 8 4 9 2 10 5 11 1 12 6 13 3 14 7 15)>
[9] [head:9] #<circular-list (0 16 8 17 4 9 2 10 5 11 1 12 6 13 3 14 7 15)>
[1] [head:2] #<circular-list (0 16 8 17 4 18 9 2 10 5 11 1 12 6 13 3 14 7 15)>
[2] [head:10] #<circular-list (0 16 8 17 4 18 9 19 2 10 5 11 1 12 6 13 3 14 7 15)>
[3] [head:5] #<circular-list (0 16 8 17 4 18 9 19 2 20 10 5 11 1 12 6 13 3 14 7 15)>
[4] [head:11] #<circular-list (0 16 8 17 4 18 9 19 2 20 10 21 5 11 1 12 6 13 3 14 7 15)>
[5] [head:1] #<circular-list (0 16 8 17 4 18 9 19 2 20 10 21 5 22 11 1 12 6 13 3 14 7 15)>
[6] [head:20] #<circular-list (0 16 8 17 4 18 19 2 20 10 21 5 22 11 1 12 6 13 3 14 7 15)>
[7] [head:10] #<circular-list (0 16 8 17 4 18 19 2 24 20 10 21 5 22 11 1 12 6 13 3 14 7 15)>
[8] [head:21] #<circular-list (0 16 8 17 4 18 19 2 24 20 25 10 21 5 22 11 1 12 6 13 3 14 7 15)>
[9] [head:5] #<circular-list (0 16 8 17 4 18 19 2 24 20 25 10 26 21 5 22 11 1 12 6 13 3 14 7 15)>
32
```

Being able to visualize a problem helps a lot...

> **Part 2:** Try again with 100x as many marbles.

If part 1 was solved efficiently (which is why I spent a while on `circular-list` in the first place...), this is just a matter of running it:

```bash
$ racket marble-madness.rkt --players 477 --stop-at 7085100

3009951158
```
