---
title: "AoC 2018 Day 5: Alchemical reduction"
date: 2018-12-05
programming/languages:
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [Alchemical Reduction](https://adventofcode.com/2018/day/5)

> **Part 1:** Given a string, reduce it by removing pairs of letters that are the same letter but different cases. Repeat until you have a minimal string.

<!--more-->

This is the sort of problem Racket excels at: it's basically a list processing problem. First, we want to define a helper function to test for reactions:

```racket
; Two units react if they are the same type (letter) and opposite polarity (case)
(define (react? a b)
  (and (not (eq? a b))
       (eq? (char-downcase a)
            (char-downcase b))))
```

After that, the core recursive function that will take a a list of characters and react through it once. This isn't quite enough to solve the problem (since after removing characters you might expose a new pair), but will do most of it:

```racket
; Collapse all unit pairs that can one time
(define (collapse-once ls)
  (match ls
    ; If The first two units react, remove them
    [(list-rest a b rest)
     #:when (react? a b)
     (collapse-once rest)]
    ; Otherwise, if we have at least one item, process the rest
    [(list-rest a rest)
     (list* a (collapse-once rest))]
    ; Base case: nothing left
    [else
     ls]))
```

I really like {{< doc racket match >}}. It's really powerful for things like this, especially with the addition of the `#:when` clause (which I actually just learned/re-learned about today). I'll be using more of that!

Now, we just need a function that will collapse until it cannot any more:

```racket
Collapse until there's nothing more to do
(define (collapse ls)
 (let ([ls^ (collapse-once ls)])
   (if (equal? ls ls^)
       ls
       (collapse ls^))))

(define input-polymer (string->list (read-line)))
(define output-polymer (collapse input-polymer))
(printf "[part 1] output length: ~a\n" (length output-polymer))
```

> **Part 2:** If you're allowed to remove one letter (both cases), what is the letter you can remove to get the smallest collapsed output (and that output's length).

Let's just brute force it. Write a helper that can remove both cases of a letter from the string and try every letter of the alphabet:

```racket
; Remove all instances of a unit (either polarity)
(define (remove/ignore-case ls c)
  (filter (λ (a) (not (eq? (char-downcase a) (char-downcase c)))) ls))

; Try removing each letter in turn, recording each new best
(define-values (best-to-remove best-length)
  (for*/fold ([best-to-remove #f]
              [best-length +inf.0])
             ([to-remove (in-string "abcdefghijklmnopqrstuvwxyz")]
              [length (in-value (length (collapse (remove/ignore-case input-polymer to-remove))))]
              #:when (< length best-length))
    (values to-remove length)))

(printf "[part 2] removing ~a gives a length of: ~a\n" best-to-remove best-length)
```

It's a bit slow (a couple seconds per collapse, but it has to do 27 of them for the two parts), but it's certainly workable:

```bash
$ cat input.txt | time racket alchemical-collapser.rkt

[part 1] output length: 9078
[part 2] removing u gives a length of: 5698
       36.88 real        32.77 user         1.07 sys
```

Well within a minute (my baseline for 'efficient enough' for these sort of problems).

I do wonder though if there's a faster way to solve this part? I bet there is. Probably something to do with {{< wikipedia "graph theory" >}}. It's always graph theory.

A problem for another day.

> **Update 2018-12-10:** Got a command (below): Can you use a stack to solve this problem?

Why yes. Yes you can! Let's do it.

All we actually have to change is the `collapse` function. What we're going to do is move elements from an `input` list to an `output` list. Whenever the top element of each list/stack reacts, remove them both. This will allow reactions to cascade natively:

```racket
; Collapse an alchemical polymer removing matching units of opposite polarity
(define (collapse polymer)
  (let loop ([input polymer]
             [output '()])
    (cond
      ; End condition, output the stack
      [(null? input) (reverse output)]
      ; Initial state, nothing on the output stack to compare
      [(null? output)
       (loop (rest input) (list (first input)))]
      ; Top of stack and next of input match, remove both
      ; This will allow chain reactions since it exposes a new top of stack to react
      [(react? (first input) (first output))
       (loop (rest input) (rest output))]
      ; Don't react, move to output
      [else
       (loop (rest input) (list* (first input) output))])))
```

And that's it; the rest of the code remains the same. We don't even need a wrapper function to collapse multiple time, this just does it.

And the crazy thing is just how much faster it is:

```bash
$ cat input.txt | time racket alchemical-collapser.rkt

[part 1] output length: 9078
[part 2] removing u gives a length of: 5698
       33.44 real        32.64 user         0.68 sys

$ cat input.txt | time racket alchemical-stacker.rkt

[part 1] output length: 9078
[part 2] removing u gives a length of: 5698
        0.54 real         0.45 user         0.08 sys
```

Now that's a speedup... Most of which comes from not having to process the entire list over and over again, instead just doing it all at once. It really does show just how much difference you can get by coming at a problem from an algorithmically different direction. 

Thanks!
