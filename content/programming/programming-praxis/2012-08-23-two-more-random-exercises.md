---
title: Two More Random Exercises
date: 2012-08-23 14:00:27
programming/languages:
- Scheme
programming/sources:
- Programming Praxis
---
Programming Praxis put out [the previous]({{< ref "2012-08-22-two-random-exercises.md" >}}) had us composing already existing PRNGs).

<!--more-->

The first function is the middle square PRNG. Basically, you start with a seed with an even number of digits and then repeatedly square it and return the middle digits.

Here I have a function that will take any suitable seed and generate a sequence of psuedorandom numbers from it:

```scheme
; middle square PRNG: square the seed and take the middle digits
(define (make-middle-square n)
  (lambda ()
    (let ([digits (inexact->exact (ceiling (log n 10)))])
      (let ([res (mod (div (* n n) 
                        (expt 10 (/ digits 2))) (expt 10 digits))])
        (set! n res)
        res))))
```

An example of running it (using the same seed from the [[wiki:Middle square|Wikipedia page]]()):

```
~ (define middle-square (make-middle-square 675248))

~ (middle-square)
 959861

~ (middle-square)
 333139

~ (middle-square)
 981593

~ (middle-square)
 524817

~ (middle-square)
 432883
```

The second example is perhaps even simpler. This time you start with any odd seed and apply the relation x<sub>n+1</sub> = 65539 * x<sub>n</sub> mod 2<sup>31</sup>:

```scheme
; randu PRNG: x_n+1 = 65539 * x_n mod 2^31 (assume x_0 is odd)
(define make-randu
  (let ([2**31 (expt 2 31)])
    (lambda (x)
      (lambda ()
        (let ([res (mod (* 65539 x) 2**31)])
          (set! x res)
          res)))))
```

An example run:

```
~ (define randu (make-randu 675249))

~ (randu)
 1305471251

~ (randu)
 1384299321

~ (randu)
 851521963

~ (randu)
 1240372481

~ (randu)
 1926020867
```

Pretty neat. Fortunately or not, this makes me want to implement a more heavyweight PRNG now, perhaps like the [[wiki:Mersenne Twister]](). We'll see.

If you'd like to download the full source code, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/two-more-random-exercises.ss">two more random exercises source</a>