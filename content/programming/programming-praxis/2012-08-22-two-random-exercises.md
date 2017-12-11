---
title: Two Random Exercises
date: 2012-08-22 14:00:47
programming/languages:
- Scheme
programming/sources:
- Programming Praxis
---
[here](https://github.com/jpverkamp/small-projects/blob/master/blog/random.ss).

First, let's make a function that can turn any die into an unfair coin. Basically, return #t / true if and only if you roll the die twice and get the same result:

```scheme
; given any random die and a possible outcome
; turn it into an unfair coin
(define (die->coin possible die)
  (lambda ()
    (eq? possible (die))))
```

From here, use the same idea that I posted about earlier to turn that unfair coin into a fair 50/50 coin:

```scheme
; given any coin, return a fair 50/50 coin
(define (coin->fair-coin coin)
  (lambda ()
    (let loop ([a (coin)]
               [b (coin)])
      (if (or (and a (not b))
              (and b (not a)))
          a
          (loop (coin) (coin))))))
```

Next, need to take that fair coin and randomly and uniformly choose an element from a list. The idea I have here is to repeatedly filter the list, removing each element with the 50/50 chance a fair coin gives us. If we have more than one element left over, repeat. If we end up with exactly one element left, that's what we return. If we remove all of the elements, start over. 

```scheme
; given a fair 50/50 coin, randomly choose an item uniformly from a list
(define (fair-coin->uniform coin ls)
  (let loop ([l ls])
    (cond
      [(null? l) (fair-coin->uniform coin ls)]
      [(null? (cdr l)) (car l)]
      [else (loop (filter (lambda (_) (coin)) l))])))
```

Finally, put everything together to turn one random generator into another:

```scheme
; now, convert one random die to another
; assume that rand-in can generate a 1 and that max-out is n for [1..n]
(define (rand->rand rand-in max-out)
  (fair-coin->uniform
    (coin->fair-coin
      (die->coin 1 rand-in))
    (map add1 (iota max-out))))
```

Now that we have the entire framework, we can solve the original problem:

```scheme
; now, actually do the problem
(define (rand3) (add1 (random 3)))
(define (rand5) (add1 (random 5)))
(define (rand9) (rand->rand rand3 9))
(define (rand7) (rand->rand rand5 7))
```

It works, but just to be sure, let's test it:

```scheme
; remove duplicates
(define (unique l)
  (fold-right (lambda (x l) (if (member x l) l (cons x l))) '() l))

; helper to test if a die is uniform with n rounds of testing
(define (test-uniform die n-rounds)
  (let ([ls (map (lambda (_) (die)) (iota n-rounds))])
    (for-each
      (lambda (i)
        (printf "~a = ~a%\n"
          i
          (* 100.0 (/ (length (filter (lambda (n) (= n i)) ls)) n-rounds))))
      (sort < (unique ls)))))
```

The results...

```

~ (test-uniform rand9 1000000)
1 = 11.07%
2 = 11.14%
3 = 11.06%
4 = 11.12%
5 = 11.10%
6 = 11.14%
7 = 11.14%
8 = 11.11%
9 = 11.16%

~ (test-uniform rand7 1000000)
1 = 14.28%
2 = 14.28%
3 = 14.30%
4 = 14.23%
5 = 14.32%
6 = 14.31%
7 = 14.28%

```

Looks pretty good to me!

(Granted, it's really slow. But it does work! :smile:)

You can get the full source [here](https://github.com/jpverkamp/small-projects/blob/master/blog/random.ss).
