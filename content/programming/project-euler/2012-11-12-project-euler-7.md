---
title: Project Euler 7
date: 2012-11-12 14:00:50
programming/languages:
- Racket
- Scheme
programming/sources:
- Project Euler
---


> By listing the first six prime numbers: 2, 3, 5, 7, 11, and 13, we can see that the 6th prime is 13.

> What is the 10 001st prime number?
> -- <cite><a href="http://projecteuler.net/problem=7">PROJECT EULER #7</a></cite>

<!--more-->

This is pretty straight forward if you can write a function that just generates prime numbers, so we'll start with that. I've dealt with prime numbers in the past (particularly in [The Sum Of The First Billion Primes]({{< ref "2012-11-01-the-sum-of-the-first-billion-primes.md" >}})), but we'll go over it quickly here again.

First, a function to test if a number is prime. The simplest test will be just to try to divide by every number. We only have to 2 and odd numbers (as any other even multiple would contain 2) and we only have to go up to the square root (as otherwise we'd already have found the other multiple), but other than that, we're not going to optimize it.

First in Racket:

```scheme
; test if n is prime by trial division
(define (prime? n)
  (or (= n 2)
      (and (not (divides? n 2))
           (for/and ([i (in-range 3 (+ 1 (ceiling (sqrt n))) 2)])
             (not (divides? n i))))))

; test if n divides m
(define (divides? m n)
  (= 0 (remainder m n)))
```

And also in Python. I had a comment offline that perhaps I should include more than one language for those that don't read Scheme (**le gasp!**), and I figure that Python's relatively easy to read even for non-coders, particularly when written in a slightly more functional style than is perhaps the standard.

```python
def is_prime(n):
    '''Test if a number is prime by simple trial division.'''

    if n == 2: return True
    elif n % 2 == 0: return False
    for i in xrange(3, 1 + int(n ** 0.5), 2):
        if n % i == 0: return False

    return True
```

After that, the next step is writing a function that, given a number, will return the next prime number. Straight forward in both cases (although you have to be careful to add one at the start so that you don't keep returning the same prime over and over):

```scheme
; return the next prime after a given number
(define (next-prime n)
  (let loop ([n (+ n 1)])
    (if (prime? n)
        n
        (loop (+ n 1)))))
```

```python
def next_prime(n):
    '''Return the next prime after a given number.'''

    n += 1
    while not is_prime(n):
        n += 1

    return n
```

Now we can use that function in a loop to return the nth prime:

```scheme
; return the nth prime
(define (nth-prime n)
  (let loop ([n n] [p 1])
    (if (= n 0)
        p
        (loop (- n 1) (next-prime p)))))
```

```python
def nth_prime(n):
    '''Return the nth prime number.'''

    p = 1
    for i in xrange(n):
        p = next_prime(p)

    return p
```

So how does it work? We know from the problem statement that the 6th prime should be 13:

```scheme
> (nth-prime 6)
13
```

```python
>>> nth_prime(6)
13
```

Good to go. So what's the 10,001st prime?

```scheme
> (time (nth-prime 10001))
cpu time: 312 real time: 310 gc time: 0
104743
```

```python
>>> time("nth_prime(10001)")
0.21 seconds
104743
```

(I need to work on / find a better Python timing module, but the point is that it's still well under a second. So all good there.)

So there you have it, the 7th Project Euler problem. Definitely more interesting than the last one at least. :smile:

As always, you can download my code for this or any Project Euler problem I’ve uploaded <a href="https://github.com/jpverkamp/small-projects/tree/master/project-euler" title="GitHub: jpverkamp: Project Euler">here</a>.
