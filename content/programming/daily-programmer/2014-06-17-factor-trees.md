---
title: Factor trees
date: 2014-06-17 14:00:59
programming/languages:
- Racket
- Scheme
programming/sources:
- Daily Programmer
programming/topics:
- Data Structures
- Prime Numbers
- Trees
---
Another five minute challenge[^1], this time from <a href="http://www.reddit.com/r/dailyprogrammer/comments/284uhh/6142014_challenge_166b_intermediate_prime_factor/">/r/dailyprogrammer</a>: given any positive integer, create and render a factor tree.

<!--more-->

The basic idea is straight forward enough. Each positive integer of note[^2] is in one of two classes: either it is [[wiki:Prime number|prime]]() or a [[wiki:Composite number|composite]](). For the composite numbers, there are at least two numbers *m* and *n* such that neither *m* nor *n* is 1 and *mn* equals that number. For example, 6 is composite because *2 * 3 = 6*, yet 5 is not, since the only numbers that divide it are 1 and itself. Since 5 is not composite, it only makes sense that it is prime.

But then, what if you have a bigger number, such as 24. You can break that into *4 * 6*. But neither of those is prime, so you can further break it into *(2 * 2) * (2 * 3)*. Finally, each of those is prime. All together, that makes up what is called a [[wiki:factor tree]]():

{{< figure src="/embeds/2014/tree-24.png" >}}

That's the challenge this week. Generate that tree.

Well, that's more than enough description. Let's get to it.

Basically, there's a quick (albeit not perfectly efficient) way to find factors: [[wiki:trial division]](). Basically, you loop through all of the numbers from 2 to the square root of the number (any larger and you'll find factors you've already found), trying to divide by each in turn. That though, generates this image rather than the previous:

{{< figure src="/embeds/2014/tree-24-small.png" >}}

Not quite as nice and balanced. Easily fixed though. Rather than looping from 2 up, loop from the square root down. You'll find the same factors, but you'll find the largest (and thus the most likely split) first.

Code:

```scheme
; Return a tree of the factors of n
(define (factor-tree n)
  (or
   ; Try to find the first pair of factors
   ; Start from sqrt(n) and work down to get the largest factors first
   (for/first ([i (in-range (integer-sqrt n) 1 -1)]
               #:when (zero? (remainder n i)))
     ; Factor, create a tree with that node and it's further factors
     (list n
           (factor-tree i)
           (factor-tree (quotient n i))))
   ; If for/first returns #f there are no other factors, n is prime
   n))
```

The comments should be straight forward enough to explain the rest of the structure. `for/first` will return the first factor that we've found (if any) or `#f` if not (which then falls through to the next case).

That gives us this structure:

```scheme
> (factor-tree 24)
'(24 (4 2 2) (6 2 3))
```

It's perhaps a bit odd to read, but look at the first of each triple. 24 has factors 4 and 6. 4 has factors 2 and 2, 6 has 2 and 3. A bit larger example (formatted to make it a bit easier to read):

```scheme
> (factor-tree 1767150)
'(1767150 (1309 17
                (77 7 11))
          (1350 (30 5 (6 2 3))
                (45 5 (9 3 3))))
```

{{< figure src="/embeds/2014/tree-1767150.png" >}}

Speaking of which, how am I getting those nice images?

Well, to some extent, I'm cheating. I took the code that I'd written a while ago for the <a href="https://github.com/iu-c211/c211-libs/blob/master/c211-libs/tree.rkt">c211-lib/tree</a> library, designed to render trees. All I needed to do was rewrite the `match` to match against `list` instead of `tree`:

```scheme
; Render a tree structure
; Tree : (U (List Integer Tree Tree) Integer)
(define (render-factor-tree tr)
  (match tr
    ; Recursive tree, unpack the value and render subtrees
    [(list factor left right)
     (define v (text (~a factor)))
     (define l (render-factor-tree left))
     (define r (render-factor-tree right))
     ; Pin-line connects the nodes, append sets the trees side by side
     ; cb/ct-find tells the pins how to connect to the nodes (center bottom/top)
     (pin-line (pin-line (vc-append 10 v (ht-append 10 l r))
                         v cb-find
                         l ct-find)
               v cb-find
               r ct-find)]
    ; Values are directly rendered
    [prime
     (text (~a prime))]))
```

The interesting parts are the functions `text` which turns text into an image, `pin-line` which draws lines between two images, and `vc-append` / `ht-append` to combine them vertically centered or horizontal aligned to the top. All together, it lets us render all sorts of nice trees:

```scheme
> (render-factor-tree (factor-tree 828441))
```

{{< figure src="/embeds/2014/tree-828441.png" >}}

```scheme
> (render-factor-tree (factor-tree 863029))
```

{{< figure src="/embeds/2014/tree-863029.png" >}}

```scheme
> (render-factor-tree (factor-tree 1048576))
```

{{< figure src="/embeds/2014/tree-1048576.png" >}}

And that's about it. Quick enough (even if the rendering probably took a bit more than five minutes when I first wrote it). As always, you can see the entire code for this (and most of my other small projects) on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/factor-tree.rkt">factor-tree.rkt</a>

[^1]: I have a few longer posts in the works, I promise
[^2]: I don't quite recall how 1 is treated
