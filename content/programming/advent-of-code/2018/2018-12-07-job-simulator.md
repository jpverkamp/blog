---
title: "AoC 2018 Day 7: Job Simulator"
date: 2018-12-07
programming/languages:
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [The Sum of Its Parts](https://adventofcode.com/2018/day/7)

> **Part 1:** Given a list of job dependencies (job A must be before job B), determine the order jobs must be done in. Break ties lexicographically.

<!--more-->

The input always has the form `Step C must be finished before step A can begin.`, so let's load that into a hash of `EDGES` and a set of `NODES`:

```racket
(define-values (EDGES NODES)
  (for/fold ([edges (hash)]
             [nodes (set)])
            ([line (in-lines)])

    (define parts (string-split line))
    (define pre (list-ref parts 1))
    (define post (list-ref parts 7))

    (values (hash-update edges
                         post
                         (curryr set-add pre)
                         (set))
            (set-add (set-add nodes pre) post))))
```

After that, we can write a few layers of helper functions. First, given a set of jobs we've already `done`, create a predicate that determines if a given job/`node` is one we `can-do?`.

```racket
; Tests if a given node can be done right now given already done nodes
(define (can-do? node done)
  (for/and ([pre (in-set (hash-ref EDGES node (set)))])
    (set-member? done pre)))
```

Using that, we can loop across all jobs that we haven't done yet and return those that we can do (that have no prerequisites not done yet):

```racket
; Get a set of nodes that can be done next
(define (possible todo done)
  (for/set ([node (in-set todo)]
            #:when (can-do? node done))
    node))
```

This will occasionally have ties though, so we need a function that will take that set of jobs and return the one that has the lowest / lexicographically first letter:

```racket
; Get the lexiographically first node in a set
(define (lex-first nodes)
  (first (sort (set->list nodes) string<?)))
```

And that's enough for part 1:

```racket
; Main body: do nodes one at a time
; Each time take the lexiographically first node that has no more dependencies
(printf "[part1] ")
(apply string-append
       (let loop ([todo NODES]
                  [done (set)]
                  [order (list)])
         (cond
           ; Base case, return order
           [(set-empty? todo) (reverse order)]
           ; Otherwise, find the next node
           [else
            (define next (lex-first (possible todo done)))
            (loop (set-remove todo next)
                  (set-add done next)
                  (list* next order))])))
```

Essentially, we get the lexicographically first node that's `possible` to do next, then move that from `todo` to `done`. Neato.

```bash
$ cat input.txt | racket graph-blocker.rkt

[part1] "OVXCKZBDEHINPFSTJLUYRWGAMQ"
```

> **Part 2:** Each job now takes time equal to 60 + (1 for A, 2 for B, etc). With 5 workers that can do jobs at once, how long does it take to finish all of the jobs?

Oh, that's interesting. The plan of attack will be to modify each of the functions from part 1 to take an optional timestamp. In addition, rather than being a `set`, `done` will now be a `hash` of job ID -> time finished. That way (with the timestamp), we know if at a given point in time a job is done.

```racket
; Tests if a given node can be done right now given already done nodes
; Done is a hash of node -> timestamp
(define (can-do? node done timestamp)
  (for/and ([pre (in-set (hash-ref EDGES node (set)))])
    (<= (hash-ref done pre +inf.0) timestamp)))

; Get a set of nodes that can be done next
(define (possible todo done timestmap)
  (for/set ([node (in-set todo)]
            #:when (can-do? node done timestmap))
    node))
```

The `+inf.0` is there basically to deal with jobs that aren't done yet but are still precursors. I sure hope we never get to a `timestamp` of `+inf.0`...

We also need one more helper function that will take a job and determine the duration for that job:

```racket
; Job duration is 60 + (1 for A, 2 for B, etc)
(define (duration node)
  (+ 1
     (base-duration)
     (char->integer (string-ref node 0))
     (- (char->integer #\A))))
```

And with that, we can schedule the jobs. The loop is a bit more complicated this time, but essentially, we will advance one timestamp at a time until we find a point where we have both a free worker and a job that has all pre-prerequisites done (at that timestamp). We'll only assign one job per loop, so in those cases we won't advance the `timestamp`, since multiple workers can start at once:

```racket
; Main body: Simulate multiple jobs running at once
(let loop ([todo NODES]   ; Set of nodes to work on
           [done (hash)]  ; Hash of node -> time finished
           [timestamp 0]  ; Current timestamp
           [workers (for/hash ([i (in-range (workers))])
                      (values i 0))])

  ; Pre-calculate any workers/jobs that became free this tick
  (define free-workers
    (for/list ([(id finished-timestamp) (in-hash workers)]
                #:when (<= finished-timestamp timestamp))
       id))

  (define free-jobs
    (possible todo done timestamp))

  (cond
    ; Base case, work is done
    ; Return nodes sorted first by finish time then by lex
    [(set-empty? todo)
     (apply max (hash-values done))]
    ; No workers/jobs are free, just advance one tick
    [(or (null? free-workers) (set-empty? free-jobs))
     (loop todo done (add1 timestamp) workers)]
    ; We have work to do and at least one worker is first
    ; Assign one worker at a time, don't advance time
    [else
     (define next (lex-first free-jobs))
     (define next-time (+ timestamp (duration next)))
     (loop (set-remove todo next)
           (hash-set done next next-time)
           timestamp
           (hash-set workers (first free-workers) next-time))]))
```

That's a pretty cool algorithm when all is said and done.

```bash
$ cat input.txt | racket timed-graph-blocker.rkt

[part2] 955
```

Onwards!
