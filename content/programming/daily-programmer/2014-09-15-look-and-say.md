---
title: Look and Say
date: 2014-09-15
programming/languages:
- Racket
- Scheme
programming/sources:
- Daily Programmer
programming/topics:
- Algorithms
- Cellular Automata
---
Random quick post today[^1]. Basically, we want to write code to generate what's known as [[wiki:Look and Say sequence]]():


> To generate a member of the sequence from the previous member, read off the digits of the previous member, counting the number of digits in groups of the same digit. For example:



> * 1 is read off as "one 1" or 11.
> * 11 is read off as "two 1s" or 21.
> * 21 is read off as "one 2, then one 1" or 1211.
> * 1211 is read off as "one 1, then one 2, then two 1s" or 111221.
> * 111221 is read off as "three 1s, then two 2s, then one 1" or 312211.



<!--more-->

Originally, my interest in this came from a video on the excellent YouTube video series <a href="https://www.youtube.com/user/numberphile">Numberphile</a>:

{{< youtube ea7lJkEhytA >}}

Yes, that is [[wiki:John Conway]]() of [[wiki:Conway's Game of Life]](). It's well worth the watch.

Then this morning, /r/dailyprogrammer has a post: <a href="https://www.reddit.com/r/dailyprogrammer/comments/2ggy30/9152014_challenge180_easy_looknsay/">Challenge #180 [Easy] Look'n'Say</a>. Seems like it's about time. :smile:

So how do we do it? Well, essentially we're going to want a function that can recur down a list of, collecting groups of like numbers. So in the sequence `111221`, we want to collect that into `111 22 1`. Then we know how long each sequence is, `31 22 11`, which is the next number in the sequence. How's that look in code?

```scheme
; Create a look and see list by combining repeated values into count+number
; For example: 111221 becomes 3 1s, 2 2s, 1 1 => 312211
(define (look-and-say ls)
  (apply
   append
   (let count ([ls (rest ls)] [i 1] [v (first ls)])
     (cond
       [(null? ls)
        (list (list i v))]
       [(equal? (first ls) v)
        (count (rest ls) (+ i 1) v)]
       [else
        (list* (list i v) (count (rest ls) 1 (first ls)))]))))
```

The counting function will recur down the list, collecting the current count (`i`) and value (`v`) as we go. Within that recursion, there are three cases. In the first case (`(null? ls)`), we've reached the end. This makes sure that we output the last sequence. In the second (`(equal? (first ls) v)`), we have a matching number, so increment the current sequence. In the last (`else`), the number do not match. Output the current count and start a new sequence.

Let's try it out:

```scheme
> (look-and-say '(1))
'(1 1)
> (look-and-say '(1 1))
'(2 1)
> (look-and-say '(2 1))
'(1 2 1 1)
> (look-and-say '(1 2 1 1))
'(1 1 1 2 2 1)
```

Looks good. It's annoying to have to keep calling it like that though. What I'd really like to see is a Racket {{< doc racket "sequence" >}}. Luckily, this is exactly the sort of thing we can make with {{< doc racket "make-do-sequence" >}}:

```scheme
; Make an infinite sequence that generates look-and-see lists
; Use the current look-and-say list itself as both the key and value
(define (in-look-and-say [ls '(1)])
  (make-do-sequence
   (thunk
    (values
     identity       ; Current
     look-and-say   ; Next
     ls             ; Initial
     (const #t)     ; Continue from this key/value/pair
     (const #t)
     (const #t)))))
```

We're going to use the sequence itself as the 'count', which makes the first few arguments easy enough. Basically, we use `identity` to return the current value, and `look-and-say` (the function we just defined above) as the `next` function. The last three are easy as well. Since we want an infinite sequence: just always return `#t`. Done.

Given this, we can generate as long a seqence as we want:

```scheme
; Take the first chunk off of a sequence
(define (look-and-say* ls i)
  (for/list ([ls (in-look-and-say ls)]
             [_  (in-range i)])
    ls))
```

Nice. :smile:

Or we can plot some interesting information about them, say the length:

```scheme
> (plot-look-and-say length '(1) 20)
```

{{< figure src="/embeds/2014/look-and-say-length.png" >}}

Or the maximum value:

```scheme
> (plot-look-and-say (curry apply max) '(1) 20)
```

{{< figure src="/embeds/2014/look-and-say-max.png" >}}

It's interesting how it never gets beyond 3 up to 50 steps along the sequence. Unfortunately

Last thing last, pretty pictures!

```scheme
; Render a look and say sequence to a bitmap, stretching rows to the entire width
; Note: Values are clamped to between 0.0 and 1.0 before conversion. *rolls eyes*
(define (render-look-and-say ls bound)
  ; Precalculate the image data; figuring out what dimenions will we need from that
  (define ls* (look-and-say* ls bound))
  (define height (length ls*))
  (define width (length (last ls*)))

  ; Precalculated list of colors that are defined to be more visually distinct
  (define colors
    '#(#(1.00 0.70 0.00) #(0.50 0.24 0.46) #(1.00 0.41 0.00) #(0.65 0.74 0.84) #(0.75 0.00 0.12)
       #(0.80 0.63 0.38) #(0.50 0.44 0.40) #(0.00 0.49 0.20) #(0.96 0.46 0.55) #(0.00 0.32 0.54)
       #(1.00 0.48 0.36) #(0.32 0.21 0.48) #(1.00 0.55 0.00) #(0.70 0.16 0.32) #(0.95 0.78 0.00)
       #(0.50 0.09 0.05) #(0.57 0.66 0.00) #(0.35 0.20 0.08) #(0.94 0.23 0.07) #(0.14 0.17 0.09)))

  ; Generate the image, three channels are RGB
  ; Note: 4 channels is ARGB, not RGBA *rolls eyes again*
  (flomap->bitmap
   (build-flomap*
    3 width height
    (λ (x y)
      ; Pull out the correct row for the data, normalize entries to 'stretch' over the entire row
      (define row (list-ref ls* y))
      (define row-width (length row))
      (define index (quotient (* x row-width) width))
      (displayln `(,x ,y ,index ,(list-ref row index) ,row))

      (vector-ref colors (list-ref row index))))))
```

That will encode each iteration into a line of the resulting image and each different value into its own color. Something like this:

```scheme
> (scale-to 200 200 (render-look-and-say '(1) 20))
```

{{< figure src="/embeds/2014/look-and-say-20.png" >}}

Neat how there's a nice line right down the center. Although that makes sense, given that there are always an even number of values. On thing that I want to check out is those divisions that the video was talking about where two parts of a sequence can diverge and never interact again. Those would be fairly straight forward to find even, just 'tag' each part of the sequence with where it came from. Perhaps another day.

As always, code on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/look-and-say.rkt">look-and-say.rkt</a>

As a side note, here's a neat trick:

```scheme
; Create a look and say sequence with regular expressions instead of lists
(define (look-and-say/regex str)
  (regexp-replace*
   #px"(.)(\\1*)"
   str
   (λ (match block repeat) (~a (string-length match) block))))
```

Regular expressions for the win! Of course, it's an order of magnitude slower than the list version, but it's still neat.

[^1]: Don't worry, I'm still working on both [Chess Puzzles]({{< ref "2013-02-01-1gam-chesslike-1-0-did-it.md" >}}) and a followup to [Procedural Invaders]({{< ref "2014-09-14-procedural-invaders.md" >}})