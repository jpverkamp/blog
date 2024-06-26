---
title: Pandigital Sums
date: 2012-10-31 14:00:11
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Mathematics
---
Yesterday's <a href="http://programmingpraxis.com/2012/10/30/pandigital-numbers/" title="Programming Praxis: Pandigital Numbers">new post</a> from Programming Praxis asked us to find all triples *(a, b, a+b)* such that *a* and *b* are three digits and *a+b* is four and concatenating the numbers results in a [[wiki:pandigital number]]() (one with all 10 digits). After that, find the smallest individual number in any of these triples.

<!--more-->

I'm sure that there is a "smart" way to approach this problem, but honestly, it's not necessary. The maximum search space is only 900<sup>2</sup>, so we should be able to do it in a second or less. In fact:

```scheme
; find all pandigital triples (a, b, a+b)
(define (pandigital-sums)
  (for*/list ([a (in-range 100 1000)]
              [b (in-range a 1000)]
              #:when (and (< 1000 (+ a b) 10000)
                          (pandigital? (combine a b (+ a b)))))
    (list a b (+ a b))))
```

That's all there is too it. We do need the `pandigital?` and `combine` functions, but they're pretty straight forward (if not the most efficient):

```scheme
; test if a number is pandigital
; must contain each digit exactly once
(define (pandigital? n)
  (define ls (sort (digits n) <))
  (define uls (sort (unique ls) <))
  (and (= (length uls) 10)
       (equal? ls uls)))

; combine a, b, and c into a number aaabbbcccc
(define (combine a b c)
  (+ (* (+ (* a 1000)
           b)
        10000)
     c))
```

`unique`, I've shown before, but what about `digits`?

```scheme
; split a number into its digits
(define (digits n)
  (let loop ([n n] [ls '()])
    (cond
      [(< n 10)
       (cons n ls)]
      [else
       (loop (quotient n 10)
             (cons (remainder n 10) ls))])))
```

Now that we have all of that, just how many sums are there?

```scheme
> (pandigital-sums)
'((246 789 1035) (249 786 1035) (264 789 1053) (269 784 1053) (284 769 1053) 
  (286 749 1035) (289 746 1035) (289 764 1053) (324 765 1089) (325 764 1089) 
  (342 756 1098) (346 752 1098) (347 859 1206) (349 857 1206) (352 746 1098) 
  (356 742 1098) (357 849 1206) (359 847 1206) (364 725 1089) (365 724 1089) 
  (423 675 1098) (425 673 1098) (426 879 1305) (429 876 1305) (432 657 1089) 
  (437 589 1026) (437 652 1089) (439 587 1026) (452 637 1089) (457 632 1089) 
  (473 589 1062) (473 625 1098) (475 623 1098) (476 829 1305) (479 583 1062) 
  (479 826 1305) (483 579 1062) (487 539 1026) (489 537 1026) (489 573 1062) 
  (624 879 1503) (629 874 1503) (674 829 1503) (679 824 1503) (743 859 1602) 
  (749 853 1602) (753 849 1602) (759 843 1602))

> (length (pandigital-sums))
48
```

Now how do we get the smallest value out of those? Honestly, we could just take the first number we found (246). But just to be in the safe side, how about we pull apart the numbers, sort them, and take the first?

```scheme
; find the smallest number in all pandigital triples (a, b, a+b)
(define (smallest-in-pandigital-sums)
  (car (sort (apply append (pandigital-sums)) <)))

> (smallest-in-pandigital-sums)
246
```

Bam. And that's all there is to it. You can download the full source here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/pandigital-sums.rkt">pandigital sums source</a>