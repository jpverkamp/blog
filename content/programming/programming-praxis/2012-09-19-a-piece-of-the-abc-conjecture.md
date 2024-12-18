---
title: A piece of the abc conjecture
date: 2012-09-19 14:00:46
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Mathematics
---
There's been a bit of hubbub in the in the math world the last few weeks with [[wiki:Shinichi Mochizuki|Shinichi Mochizuki's]]() 500 page proof that of the [[wiki:ABC conjecture]](). Basically, the conjecture states that given three positive coprime integers *a*, *b*, and *c* such that *a* + *b* = *c*, the product of the distinct prime factors of *a*, *b*, and *c* is rarely much smaller than *c*. While this may sound strange, there are a number of interesting consequences that you can read about [[wiki:Abc conjecture#Some consequences|here]]().

To make a long story shorter, there was a challenge on <a href="http://programmingpraxis.com/2012/09/18/abc-conjecture/" title="ABC Conjecture">Programming Praxis</a> that intrigued me, which was to write code that given a upper bound on *c* would generate a list of all of the triples *(a, b, c)* such that the product is larger.

<!--more-->

I've been getting more into the hang of Racket, particularly the `for` family of macros they have, so here's my Racket code for generating such a list.

First, we could use a set of helper functions:

```scheme
; keep only unique items in a list
(define (unique l) (foldl (lambda (x l) (if (member x l) l (cons x l))) '() l))

; test if i evenly divides n
(define (div? n i) (zero? (remainder n i)))

; test if any item in l satisifies the predicate ?
(define (any? ? l) (not (null? (filter ? l))))

; return the prime factors of n
(define (factor n)
  (let loop ([i 2])
    (cond
      [(> (* i i) n) (list n)]
      [(div? n i)
       (append (factor i) (factor (/ n i)))]
      [else 
       (loop (+ i 1))])))

; calculate the greatest common demoninator of a and b
(define (gcd a b)
  (cond
    [(= a b) a]
    [(< a b) (gcd a (- b a))]
    [else (gcd (- a b) b)]))

; test if two numbers are co-prime (share no common factors except 1)
(define (coprime? a b) (= 1 (gcd a b)))
```

Next we need the two functions from the actual proof. The neat thing is that with all of the helper functions above, these have become essentially trivial to write. 

```scheme
; calculate the radical (product of unique prime factors) of a number
(define (rad n) (apply * (unique (factor n))))

; calculate the ration of radicals for a set of coprime a + b = c
(define (q a b c) (/ (log c) (log (rad (* a b c)))))
```

Finally, the meat of the function. The best part for me was using Racket's excellent `for*/list` function to build the list.

```scheme
; run the test
; for all b, for all a < b; 
;   if a+b < limit, a and b are coprime, and q > 1, store the result 
(define (abc n)
  (sort 
   (for*/list ([b (in-range 1 n)]
               [a (in-range 1 b)]
               #:when (and (< (+ a b) n)
                           (coprime? a b)
                           (> (q a b (+ a b)) 1)))
     (list (q a b (+ a b)) a b (+ a b)))
   (lambda (x y) (> (car x) (car y)))))
```

Now, to test it:

```
> (abc 1000)
'((1.4265653296335432 3 125 128)
  (1.3175706029138485 1 512 513)
  (1.311101219926227 1 242 243)
  (1.292030029884618 1 80 81)
  (1.2727904629543532 13 243 256)
  (1.226294385530917 1 8 9)
  (1.2251805398372944 1 288 289)
  (1.2039689893561185 49 576 625)
  (1.198754152359422 169 343 512)
  (1.1757189916348774 32 49 81)
  (1.1366732909394883 25 704 729)
  (1.1126941404922133 1 63 64)
  (1.1084359145429683 32 343 375)
  (1.1048460623308174 104 625 729)
  (1.0921945706283556 1 675 676)
  (1.0917548251330267 100 243 343)
  (1.0790468171894105 1 624 625)
  (1.0458626417646626 1 728 729)
  (1.0456203807611666 5 507 512)
  (1.0412424573518235 1 48 49)
  (1.0370424407259895 81 175 256)
  (1.0344309549548174 343 625 968)
  (1.0326159011595437 81 544 625)
  (1.0326070471078377 7 243 250)
  (1.0288287974277142 2 243 245)
  (1.027195810121916 4 121 125)
  (1.0251241218312794 27 512 539)
  (1.018975235452531 5 27 32)
  (1.0129028397298183 1 224 225)
  (1.0084113092374762 200 529 729)
  (1.004797211020379 1 960 961))

```

Which are exactly the results that Programming Praxis got in <a href="http://programmingpraxis.com/2012/09/18/abc-conjecture/2/" title="Programming Praxis: abc conjecture">their solution</a>, so all is well in the world. 

Just out of curiosity (since they did something clever in generating a and b while I just brute forced it) I ran timings of both of them on my machine:

```scheme
> (time (abc 1000)) ; my code
cpu time: 8206 real time: 8269 gc time: 139

> (time (abc 1000)) ; their code
cpu time: 10280 real time: 10321 gc time: 189
```

Basically, they're pretty close. Mine is a bit faster, which surprised me slightly, but it's really not that big of a difference in the grand scheme of things. 

In any case, it was a neat little exercise. Perhaps I'll go and actually read the proof of the conjecture... No, probably not. It's still an interesting result though. :smile:

If you'd like, you can download the entire source of the project here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/abc.ss" title="abc source">abc source</a>
