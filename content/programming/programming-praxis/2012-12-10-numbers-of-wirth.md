---
title: Numbers of Wirth
date: 2012-12-10 14:00:19
programming/languages:
- Python
- Racket
- Scheme
programming/sources:
- Programming Praxis
---
Niklaus Wirth gave the following problem back in 1973:

> Develop a program that generates in ascending order the least 100 numbers of the set M, where M is defined as follows:

> a) The number 1 is in M.

> b) If x is in M, then y = 2 * x + 1 and z = 3 * x + 1 are also in M.

> c) No other numbers are in M.

(via <a href="http://programmingpraxis.com/2012/12/07/wirth-problem-15-12/" title="Programming Praxis: Wirth Problem 15.12">Programming Praxis</a>)

It's an interesting enough problem, so let's work out a few different ways of doing it.

<!--more-->

First, there's the simple, brute force method. Start by writing a recursive definition to check if a number is a 'Wirth number' by reversing the two equations given in part b of the definition:

In Scheme:

```scheme
; recursively determine if a number is a wirth number
(define (wirth? n)
  (and (positive? n)
       (integer? n)
       (or (= n 1)
           (wirth? (/ (- n 1) 2))
           (wirth? (/ (- n 1) 3)))))
```

And Python:

```python
def is_wirth(n):
	'''Recursively determine if a number is a wirth number'''

	if n < 0 or n != int(n):
		return False
	elif n == 1:
		return True
	else:
		return is_wirth((n - 1) / 2.0) or is_wirth((n - 1) / 3.0)
```

With something like that, it would be easy enough to write a loop in either language that just starts at 1 and checks every number:

Scheme:

```scheme
; list the first n wirth numbers
(define (n-wirth n)
  (let loop ([i 1] [cnt 0])
    (cond
      [(= cnt n) '()]
      [(wirth? i) (cons i (loop (+ i 1) (+ cnt 1)))]
      [else (loop (+ i 1) cnt)])))
```

Python:

```python
def n_wirth(n):
	'''List the first n wirth numbers'''

	ls = []
	i = 1
	while len(ls) < n:
		if is_wirth(i):
			ls.append(i)
		i += 1

	return ls
```

Easy enough, and for the case of `n=100`, it runs pretty much instantly:

```scheme
> (time (n-wirth 100))
cpu time: 0 real time: 1 gc time: 0  
'(1    3    4    7    9    10   13   15   19   21
  22   27   28   31   39   40   43   45   46   55
  57   58   63   64   67   79   81   82   85   87
  91   93   94   111  115  117  118  121  127  129
  130  135  136  139  159  163  165  166  171  172
  175  183  187  189  190  193  202  223  231  235
  237  238  243  244  247  255  256  259  261  262
  271  273  274  279  280  283  319  327  331  333
  334  343  345  346  351  352  355  364  367  375
  379  381  382  387  388  391  405  406  409  418)
```

In fact, even until the first 10,000 such numbers it's still pretty fast:

```scheme
> (time (n-wirth 10000))
cpu time: 670 real time: 700 gc time: 63
'(...)
```

So why even bother doing better? Because we can!

The next step would be to realize that we're redoing a lot of the work in `is_wirth` / `wirth?`. This should look like the perfect opportunity to use memorization, which I just so happen to have posted about both in [Python]({{< ref "2012-09-29-pickles-and-memoization.md" >}}) and [Racket]({{< ref "2012-10-20-memoization-in-racket.md" >}}). 

Make those changes and run it again:

```scheme
> (time (n-wirth 10000))
cpu time: 218 real time: 213 gc time: 0
'(...)
```

Three times faster. None too shabby, particularly for such a relatively small runtime as it is. But there's still at least two (fairly obvious) ways to do it!

The next would be to use generators. This solution got a bit strange, so I only have a Python version. The basic idea is that for any number, we want to be able to generate the two branches of Wirth numbers from that number, merging them as we go. So first, let's start with a function that can merge two generators into a new generator (removing duplicates):

```python
def merge_generators(g1, g2):
	'''Merge two numeric generators in increasing order.'''

	n1 = g1.next()
	n2 = g2.next()
	while True:
		if n1 < n2:
			yield n1
			n1 = g1.next()
		elif n1 > n2:
			yield n2
			n2 = g2.next()
		else:
			yield n1
			n1 = g1.next()
			n2 = g2.next()
```

So for example, if we have generators for multiples of two and three:

```python
def take(gen, n):
	'''Take the first n items from a generator.'''
	ls = []
	while len(ls) < n:
		ls.append(gen.next())
	return ls

def multiples_of(n):
	'''Return multiples of n, starting at n.'''
	i = n
	while True:
		yield i
		i += n

>>> take(merge_generators(multiples_of(2), multiples_of(3)), 20)
[2, 3, 4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 26, 27, 28, 30]
```

So how do we put that all together?

```python
def wirth_gen(n):
	'''A generator for wirth numbers.'''
	yield n
	for i in merge_generators(wirth_gen(2 * n + 1), wirth_gen(3 * n + 1)):
		yield i
```

So you yield the number that you're at, then you merge the two generators. Straight forward enough. And we can use the `take` function from above to generate the first `n`:

```python
def gen_n_wirth(n):
	'''List the first n wirth numbers using generators'''
	return take(wirth_gen(1), n)
```

I have to admit, I think that's the most nested generator I've ever written. In practice though, it's faster than either of the previous Racket versions, taking only 160ms to generate the first 10,000 numbers in the sequence.

Two more options and I think I'll call it a day. The first is based pretty much directly on the sieves that I used in my original [billion primes post]({{< ref "2012-11-01-the-sum-of-the-first-billion-primes.md" >}}). Basically, create a list of natural numbers. Starting at the bottom, we'll check off the Wirth numbers, returning them as we go. The only problem is that we don't have a solid upper bound (as we did with the primes). So we'll just ask the user to supply one. Here's the code:

Racket:

```scheme
; list the first n wirth numbers with a sieve
(define (sieve-n-wirth n sieve-size)
  (define sieve (make-vector sieve-size #f))
  (vector-set! sieve 1 #t)
  (take
   (for/list ([i (in-range sieve-size)]
              #:when (vector-ref sieve i))
     (when (< (+ (* 2 i) 1) sieve-size)
       (vector-set! sieve (+ (* 2 i) 1) #t))
     (when (< (+ (* 3 i) 1) sieve-size)
       (vector-set! sieve (+ (* 3 i) 1) #t))
     i)
   n))
```

Python:

```python
def sieve_n_wirth(n, size):
	'''Generate the first n wirth numbers using a sieve.'''

	sieve = [False for i in xrange(size)]
	sieve[1] = True
	ls = []
	for i in xrange(size):
		if sieve[i]:
			ls.append(i)
			if 2 * i + 1 < size: sieve[2 * i + 1] = True
			if 3 * i + 1 < size: sieve[3 * i + 1] = True
			if len(ls) == n:
				break
	return ls
```

And timing:

```scheme
> (time (sieve-n-wirth 10000))
cpu time: 15 real time: 11 gc time: 0
'(...)
```

I don't think we're going to beat that time. 

Last but not least, priority queues / heaps. The general idea is to let the data structure do the work. Since a heap is designed to let you insert items in any order but only pull them back out in order, it's perfect for the task. You can get heaps in Python from `heapq` and in Racket from `data/heap`. Here's how you use it (there's a bit of ugliness to remove duplicates):

Racket:

```scheme
(require data/heap)

; list the first n wirth numbers with a heap
(define (heap-n-wirth n)
  (define heap (make-heap <))
  (heap-add! heap 1)
  (let loop ([n n])
    (cond
      [(zero? n) '()]
      [else
       (define i (heap-min heap))
       (heap-add! heap (+ (* 2 i) 1))
       (heap-add! heap (+ (* 3 i) 1))
       (let loop () ; remove duplicates
         (when (= i (heap-min heap))
           (heap-remove-min! heap)
           (loop)))
       (cons i (loop (- n 1)))])))
```

Python:

```python
from heapq import heappop, heappush 

def heap_n_wirth(n):
	'''Generate the first n wirth numbers using a heap.'''

	ls = []
	heap = []
	heappush(heap, 1)
	while len(ls) < n:
		i = heappop(heap)
		if not i in ls:
			ls.append(i)
			heappush(heap, 2 * i + 1)
			heappush(heap, 3 * i + 1)
	return ls
```

And timing:

```scheme
> (time (heap-n-wirth 10000))
cpu time: 562 real time: 557 gc time: 157
'(...)
```

And we're back to the original runtime. So the sieved version still wins out. 

If you have any particularly different algorithms (or any improvements to my versions above), be sure to let me know in the comments.

As always, you can download the full code for today's post from GitHub:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/numbers-of-wirth.py" title="Numbers of wirth source (python)">Python source</a>
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/numbers-of-wirth.rkt" title="Numbers of wirth source (Racket)">Racket source</a>