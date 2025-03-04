---
title: Project Euler 9
date: 2012-11-15 14:00:35
programming/languages:
- Racket
- Scheme
programming/sources:
- Project Euler
---


> A Pythagorean triplet is a set of three natural numbers, a  b  c, for which,

> a<sup>2</sup> + b<sup>2</sup> = c<sup>2</sup>

> For example, 3<sup>2</sup> + 4<sup>2</sup> = 9 + 16 = 25 = 5<sup>2</sup>.

> There exists exactly one Pythagorean triplet for which a + b + c = 1000.

> Find the product abc.
> -- <cite><a href="http://projecteuler.net/problem=9">PROJECT EULER #9</a></cite>

<!--more-->

I like it. :smile:

I've already done a [much larger problem]({{< ref "2012-10-27-pythagorean-triples.md" >}}) on [[wiki:Pythagorean Triples]](), so this one should be pretty straight forward. Essentially, since we know that an answer exists, we need to just go through all of the triples in some sensible order until we find the one that we want.

Starting with Python this, time, we can represent that idea pretty directly with a generator (a function that when called multiple times returns a (potentially) different answer for each call):

```python
def pythagorean_triplets():
    '''Generate all pythagorean triples with a < b, ordered by b.'''

    b = 0
    while True:
        b += 1
        for a in xrange(1, b + 1):
            c = math.sqrt(a * a + b * b) 
            if c == int(c):
                yield a, b, int(c)
```

The idea here is to loop through all natural numbers for `b`. For each of those, loop through all values for `a` up to (and including) `b`. For each, calculate `c` and check if it's an actual integer solution. If it is, `return` it (in this case, we use `yield` rather than `return` to signify that this is a generator and to '`return`' multiple results). 

From here, we want to write a general function that, given any number n, will find a Pythagorean triple such that `a+b+c = n`. The power of Python's generators is that we can directly use them in a loop:

```python
def pythagorean_sum_equals(n):
    '''Find all pythagorean triples where a+b+c = n.'''

    for a, b, c in pythagorean_triplets():
        if a + b + c == n:
            return a, b, c
        elif b > n:
            return #f
```

The last bit there says that if we've already advanced be past n, we know that there's no chance for finding a valid sum as all future sums are greater than n. We could probably stop a bit sooner than that, but since we're looking at the moment for a sum that we know exists, we don't have to.

Let's try it out with the smallest Pythagorean Triple. We should just get the triple right back out. 

```python
>>> pythagorean_sum_equals(3 + 4 + 5)
(3, 4, 5)
```

Good to go. So, let's use this to actually solve the problem:

```python
def problem_0009():
    a, b, c = pythagorean_sum_equals(1000)
    return a * b * c
```

And try it out:

```python
>>> problem_0009()
31875000
```

Exactly what we were looking for. And it only took 36 milliseconds to calculate. That's pretty good. Judging from a comment on the previous Pythagorean Triples post, generators are expensive, so let's try it without:

```python
def pythagorean_sum_equals_nogen(n):
    '''Find all pythagorean triples where a+b+c = n.'''

    b = 0
    while True:
        b += 1
        for a in xrange(1, b + 1):
            c = math.sqrt(a * a + b * b) 
            if c == int(c) and a + b + c == n:
                return a, b, c
```

It turns out though, that while this code is faster, it's only 3 milliseconds (about 10% faster), well within the threshold for noise for this sort of problem. We'll keep trying on future problems though, on some of them that take longer to run, it may become necessary.

Now that we've gotten the solution worked out in Python, let's work it out in Racket. I'm just going to go straight for the non-generator version here, since I do know that generators in Racket are more expensive.

```scheme
(define (pythagorean-sum-equals n)
  (call/cc
   (lambda (return)
     (for* ([b (in-naturals 1)]
            [a (in-range 1 (+ b 1))])
       (define c (sqrt (+ (* a a) (* b b))))
       (when (and (integer? c)
                  (= n (+ a b c)))
         (return (* a b c)))))))
```

There are two interesting points here. The first is the use of `call/cc` to bail out of the function whenever I find a solution, much as I did back in the solution to [4sum]({{< ref "2012-08-27-4sum.md" >}}). `call/cc` is a fascinating beast all it's own, but all you need to know at this point is that it will take whatever would be done 'next' where it's called (in this case, returning from the function) and pass it along as an argument. So in this case, `return` has the same meaning that it would in Python or the like, although I could have chosen anything for that name. 

The second intersting thing is the `for*` macro. Rather than zipping the two variables as a normal `for` would, `for*` automatically nests them, so that you get the exact same nested looping structure that we had in the Python version, only in two lines rather than 4. 

After that, the core of the loop is the same, so we should theoretically get the same answer:

```scheme
> (time (pythagorean-sum-equals 1000))
cpu time: 24 real time: 24 gc time: 0
31875000
```

So we do. And it's marginally faster, which I would say is probably the general case between Python and Racket. We'll see though, particularly as the problems get even more interesting.

As always, you can download my code for this or any Project Euler problem I’ve uploaded <a href="https://github.com/jpverkamp/small-projects/tree/master/project-euler" title="GitHub: jpverkamp: Project Euler">here</a>.
