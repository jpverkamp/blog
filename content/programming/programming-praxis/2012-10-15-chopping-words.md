---
title: Chopping words
date: 2012-10-15 14:00:13
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Backtracking
- Word Games
---
<a title="Programming Praxis: Chopping Words" href="http://programmingpraxis.com/2012/07/03/chopping-words/">One more challenge</a> from Programming Praxis' <a title="Programming Praxis: Themes: Word Games" href="http://programmingpraxis.com/contents/themes/#Word Games">Word Games</a> today (there are only a few left!). This time we have the challenge of cutting off bits of words, one letter at a time, such that each step is still a word.

The example given in their post is `planet → plane → plan → pan → an → a`, although surely many such examples exist.

<!--more-->

This one looks really simple on the surface--use the same backtracking algorithms that we've been using all along with the [dictionary code]({{< ref "2012-10-11-dictionary-tries-in-racket.md" >}}) previously described to verify words at each step. Let's see if it really is that simple.

First, we want to be able to cut a single character out of a string, leaving the rest untouched. Basically, choose a random character in the string. Then make a new string, copying letters from before the random character directly and those after offset by one:

```scheme
; chop a given character from a string
(define (chop s i)
  (list->string
   (for/list ([n (string-length r)])
     (string-ref s (if (< n i) n (+ n 1))))))
```

Now we can solve the problem. I'm going for a slightly more in depth problem; rather than just finding one such chain of words, I want to find all of them. The idea is to start at each level by finding the strings with one letter chopped that are still words. For each of those recur. By the power of recursion, you should either get a tree of chopped words from that point or an empty list. If you get the former, add our word to it; the latter, pass the empty list along.

```scheme
; repeatedly chop so long as all chops are words
(define (chopping-words dict word)
  (if (= 1 (string-length word))
      (list word)
      (let ([recur (for/fold ([ans '()])
                             ([i (string-length word)]
                              #:when (contains? dict (chop word i)))
                     (let ([each (chopping-words dict (chop word i))])
                       (if (null? each)
                           ans
                           (cons each ans))))])
        (if (null? recur)
            '()
            (cons word recur)))))
```

Seems sensible enough. The `for/fold` is an interesting construct that I hadn't used before, but it's not too bad. Basically, instead of just the looping variables of a normal `for`, you have a first block storing the accumulators--in this case `ans`. Each iteration of the loop should return the next value (or `values`) for the accumulators(s). Add in the case at the end for either building the tree or passing the empty list up the chain and you're good to go.

Let's try it out:

```scheme
> (chopping-words dict "PLANET")
'("PLANET"
  ("PLANE"
   ("PLAN" ("PAN" ("PA" ("A")) ("AN" ("A"))))
   ("PANE" ("PAN" ("PA" ("A")) ("AN" ("A")))))
  ("PLANT"
   ("PLAN" ("PAN" ("PA" ("A")) ("AN" ("A"))))
   ("PLAT" ("PAT" ("PA" ("A")) ("AT" ("A"))))
   ("PANT"
    ("PAN" ("PA" ("A")) ("AN" ("A")))
    ("PAT" ("PA" ("A")) ("AT" ("A")))
    ("ANT" ("AN" ("A")) ("AT" ("A"))))))
```

Looks pretty good. :smile: As you may have guessed, you're going to need a word containing either `A` or `I` for there to be a valid tree at all. Still, pretty neat though. An even more interesting trick would be to generate a graph rather than a tree, branching out from the initial word and eventually collapsing back into the one or two final states. In this case, there would be a single final state and only three states before that: `PA`, `AN`, and `AT`. Perhaps we'll leave that for another day.

The code is short enough today that I don't have a full source code download. You can just copy/paste the code into Racket to try it out for yourself. Don't forget the `(require "[dictionary.rkt]({{< ref "2012-10-11-dictionary-tries-in-racket.md" >}})")` line though, otherwise `contains?` isn't likely to work so well. :smile:
