---
title: "Dodgson\u2019s Doublets"
date: 2012-10-14 14:00:20
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Backtracking
- Word Games
slug: dodgsons-doublets
---
Today we have [doublets source code](https://github.com/jpverkamp/small-projects/blob/master/blog/doublets.rkt), [dictionary source code](https://github.com/jpverkamp/small-projects/blob/master/racket-libraries/dictionary.rkt), [queue source code](https://github.com/jpverkamp/small-projects/blob/master/racket-libraries/queue.rkt).

Using the same source code as the previous two posts ([here]({{< ref "2012-10-11-squaring-the-bishop.md" >}}) and [here]({{< ref "2012-10-13-word-cubes.md" >}}), described originally [here]({{< ref "2012-10-11-dictionary-tries-in-racket.md" >}})) for the dictionary, the code is a pretty straight forward case of using [[wiki:recursion]]() to do [[wiki:backtracking]](). Basically, try all of the possible next words one letter different. Whenever you find a dead end, back up and try a different path. Something like this:

```scheme
; find the path between two words, changing one letters at a time
; use call/cc to bail out when we find an answer
(define (direct-doublet dict src dst)
  (call/cc
   (λ (exit)
     (let ([src (string-upcase src)]
           [dst (string-upcase dst)])
       ; loop down possible solutions
       (let loop ([current src] [words (list src)])
         ; when we find one, bail out entirely
         (if (equal? current dst)
             (exit (reverse words))
             ; try all possible values
             (for*/list ([i (string-length src)]
                         [c "ABCDEFGHIJKLMNOPQRSTUVWXYZ"])
               (let ([next (string-set current i c)])
                 (when (and (not (member next words))
                            (contains? dict next))
                   (loop next (cons next words))))))))
     (exit #f))))
```

Basically, I'm using a neat trick I last used on the post about [4SUM]({{< ref "2012-08-27-4sum.md" >}}) where `call/cc` lets us bail out of the depths of the code as soon as we find a solution. Other than that, it's a simple matter of using `for*` to loop over each position and each character, generating all possible words. Whenever a word is valid (and not one we've seen before in this path), keep going. Eventually, we'll find a solution and can bail out. On the off chance that we don't, return `#f`.

(Side note: `string-set` is a functional version of `string-set!` that returns a new string rather than mutating the previous one in place. It's easy enough to implement or can see a version of it in the [full source](https://github.com/jpverkamp/small-projects/blob/master/blog/doublets.rkt).)

It works well enough, but there is one bit of an issue. This one performs a depth first search, following one path all of the way until it finds a solution or a dead end. Unfortunately, there are a *lot* of paths that we can take without getting close to a solution. Let's see if we can't do better.

This time, I'm going to use a simple greedy heuristic to control the solution. It's still depth first, but this time, we're going to try the words that are closest to the target first (with a small bit of random wiggle to break up equally likely solutions). Here's the differencing function:

```scheme
; calculate the difference between two strings
(define (string-diff s1 s2)
  (+ (random)
     (for/sum ([c1 s1] [c2 s2])
       (abs (- (char->integer c1) (char->integer c2))))))
```

With that, we can work out the solution:

```scheme
; find the path between two words, changing one letters at a time
; use call/cc to bail out when we find an answer
(define (doublet dict src dst)
  (call/cc
   (λ (exit)
     (let ([src (string-upcase src)]
           [dst (string-upcase dst)])
       ; loop recursively
       (let loop ([current src] [words (list src)])
         ; bail when we find any solution
         (if (equal? current dst)
             (exit (reverse words))
             ; find all of the next steps
             (let ([nexts
                    (for*/list ([i (string-length src)]
                                [c "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
                                #:when
                                (let ([next (string-set current i c)])
                                  (and (not (member next words))
                                       (contains? dict next))))
                      (string-set current i c))])
               ; sort by distance to the final solution, recur in that order
               (for ([next (sort nexts (λ (w1 w2) (< (string-diff w1 dst)
                                                     (string-diff w2 dst))))])
                 (loop next (cons next words)))))))
     (exit #f))))
```

This time we use `for*/list` instead of `for*` as we actually want to return the possible next words. We then sort them by their distance from the target and use that for the branching. It's quite a bit faster, actually solving the suggested one on Programming Praxis where they want a path from `BLACK` to `WHITE` (actually rather fast, solving it in only 16ms).

Faster, but it's still not quite optimal. The paths returned are nowhere near the shortest they could be. So let's take a totally different track. What we need is a breadth first search. We're going to keep a queue of solutions, at each loop adding any new branches to the end and taking the next try from the beginning. This will guarantee that the found solution is as short as possible.

Unfortunately, the code isn't nearly as functional as the previous solutions. To share a queue between the various branches, we need a mutable queue. Here's something that I wrote up quicklike to make it happen:

```scheme
; opaque structure for the queue
(define-struct :queue: (values head tail) #:mutable)

; create a new queue
(define (make-queue) (make-:queue: (make-hasheq) 0 0))

; test if the queue is empty
(define (queue-empty? q)
  (= (:queue:-head q) (:queue:-tail q)))

; push an item onto the queue
(define (queue-push! q v)
  (hash-set! (:queue:-values q) (:queue:-tail q) v)
  (set-:queue:-tail! q (+ 1 (:queue:-tail q))))

; pop an item from the queue and return
(define (queue-pop! q)
  (let ([v (hash-ref (:queue:-values q) (:queue:-head q))])
    (hash-remove! (:queue:-values q) (:queue:-head q))
    (set-:queue:-head! q (+ 1 (:queue:-head q)))
    v))
```

Perhaps it's not the most efficient, but it does work well enough. You can get the full source code: [queue source code](https://github.com/jpverkamp/small-projects/blob/master/racket-libraries/queue.rkt). Here's a solution to doublet that uses it:

```scheme
; find the path between two words, using a queue
; values in the queue are (current, path)
(define (breadth-doublet dict src dst)
  (call/cc
   (λ (exit)
     (let ([src (string-upcase src)]
           [dst (string-upcase dst)]
           [q (make-queue)])
       ; start with just the initial solution
       (queue-push! q (list src (list src)))
       ; loop as long as the queue isn't empty, popping the first each time
       (let loop ()
         (when (not (queue-empty? q))
           (let* ([next (queue-pop! q)]
                  [curr (car next)]
                  [wrds (cadr next)])
             ; if we find a solution, it's optimal
             (if (equal? curr dst)
                 (exit (reverse wrds))
                 (begin
                   ; find all next steps, push them onto the queue
                   (for* ([i (string-length src)]
                          [c "ABCDEFGHIJKLMNOPQRSTUVWXYZ"])
                     (let ([next (string-set curr i c)])
                       (when (and (not (member next wrds))
                                  (contains? dict next))
                         (queue-push! q (list next (cons next wrds))))))
                   (loop)))))))
     (exit #f))))
```

Most of the structure looks about the same with the same internal loop generating next words. The difference this time is that the new solutions are added to the queue and the next solution is popped from the queue.

Let's see what sort of answers we get:

```scheme
> (time (doublet dict "head" "tail"))
cpu time: 15 real time: 17 gc time: 0
'("HEAD" "READ" "REAL" "REEL" "REEK" "SEEK"
  "SEEM" "TEEM" "TEEN" "SEEN" "WEEN" "WEEK"
  "PEEK" "PEEL" "PEEN" "PEEP" "SEEP" "VEEP"
  "WEEP" "WEED" "TEED" "TEES" "TEDS" "TADS"
  "TAGS" "SAGS" "SAGO" "SAGE" "SAKE" "TAKE"
  "TALE" "TALL" "TAIL")

> (time (breadth-doublet dict "head" "tail"))
cpu time: 5070 real time: 5344 gc time: 1170
'("HEAD" "HEAL" "HEIL" "HAIL" "TAIL")

> (time (doublet dict "black" "white"))
cpu time: 15 real time: 9 gc time: 0
'("BLACK" "SLACK" "SLICK" "SLINK" "SLING" "STING"
  "SUING" "RUING" "RUINS" "REINS" "VEINS" "ZEINS"
  "PEINS" "PAINS" "PAINE" "MAINE" "MAINS" "WAINS"
  "WAITS" "WHITS" "WHITE")

> (time (breadth-doublet dict "black" "white"))
cpu time: 58890 real time: 62141 gc time: 16380
'("BLACK" "CLACK" "CLICK" "CHICK" "CHINK" "CHINE" "WHINE" "WHITE")
```

As one might expect, the depth first solution is much faster when it finds a solution but the solutions aren't optimal. The breadth first solution finds the shortest solution (or at least one tied for it, it actually found a better solution than the one given in the original description of the problem), but takes much longer.

The breadth first solution also eats up quite a lot more memory, possibly owning to my implementation of the queue. I had to up the memory allocated to Racket to get it to run, although only to 256 MB and only for the `BLACK`/`WHITE` case. Still, none too shabby.

If you'd like to see the full source code, click here: [doublets source code](https://github.com/jpverkamp/small-projects/blob/master/blog/doublets.rkt), [dictionary source code](https://github.com/jpverkamp/small-projects/blob/master/racket-libraries/dictionary.rkt), [queue source code](https://github.com/jpverkamp/small-projects/blob/master/racket-libraries/queue.rkt). It runs in <a href="http://racket-lang.org" title="(((λ Racket)))">Racket 5.3+</a>.
