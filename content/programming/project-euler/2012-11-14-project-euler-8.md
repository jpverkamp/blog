---
title: Project Euler 8
date: 2012-11-14 14:00:42
programming/languages:
- Racket
- Scheme
programming/sources:
- Project Euler
---


> Find the greatest product of five consecutive digits in the 1000-digit number.
> -- <cite><a href="http://projecteuler.net/problem=8">PROJECT EULER #8</a></cite>

<!--more-->

This is both a completely straight forward problem and a nice way to learn about scanning through strings. 

In the Racket case, we'll want to use nested `for` loops. The outer loop will use `for/fold` to keep track of the best result so far. The inner loop will take an offset into the string and calculate the product. Assuming that the string `n` contains the number given in the problem:

```scheme
(for/fold ([best 0])
          ([i (in-range (- (string-length n) 5))])
  (max best
       (for/product ([j (in-range 5)])
         (string->number (string (string-ref n (+ i j)))))))
```

The code in the Python version is pretty much the same:

```python
best = 0
for i in range(len(n) - 5):
    best = max(best, int(n[i + 0]) * 
                     int(n[i + 1]) * 
                     int(n[i + 2]) * 
                     int(n[i + 3]) * 
                     int(n[i + 4]))
print best
```

If you want to get a bit fancy about it, you can take advantage of the `reduce` function to rewrite that code in a much more compact (albeit less readable fashion):

```python
from operator import mul
print reduce(max, [reduce(mul, map(int, n[i:i+5]), 1) for i in range(len(n) - 5)], 0)
```

If you work from the inside out:

* `n[i:i+5]` will pull out five digits starting at `i` as a string
* `map(int, n[i:i+5])` will convert that into a list of five actual integers
* `reduce(operator.mul, ..., 1)` will basically combine that list into a single number using multiplication as the glue (`*` isn't a function in Python, ergo `operator.mul`)
* `[reduce(...) for i in range(len(n) - 5)]` will generate all such products
* `reduce(max, ..., 0)` will calculate the maximum of all of these numbers


Each of these versions will give you the expected value of 40824 (and all in less than a millisecond). None too shabby for a day's work. 

As always, you can download my code for this or any Project Euler problem I’ve uploaded <a href="https://github.com/jpverkamp/small-projects/tree/master/project-euler" title="GitHub: jpverkamp: Project Euler">here</a>.