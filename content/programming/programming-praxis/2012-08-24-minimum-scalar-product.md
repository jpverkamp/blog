---
title: Minimum scalar product
date: 2012-08-24 14:00:59
programming/languages:
- Scheme
programming/sources:
- Programming Praxis
---
<a title="Minimum Scalar Product" href="http://programmingpraxis.com/2012/08/10/minimum-scalar-product/">Another post</a> from Programming Praxis, this time we're to figure out what is the minimum [[wiki:scalar product]]() of two [[wiki:Vector (mathematics and physics)|vectors]](). Basically, you want to rearrange two given lists a<sub>1</sub>, a<sub>2</sub>, ..., a<sub>n</sub> and b<sub>1</sub>, b<sub>2</sub>, ..., b<sub>n</sub> such that a<sub>1</sub>b<sub>1</sub> + a<sub>2</sub>b<sub>2</sub> + ... + a<sub>n</sub>b<sub>n</sub> is minimized.

<!--more-->

It turns out though that it's a remarkably simple algorithm. Just sort the two vectors and reverse the second one:

```scheme
(define (minimum-scalar-product l r)
  (apply + (map * (sort < l) (sort > r))))
```

This will assure that the largest and smallest elements are paired, up through the smallest and largest. I don't have a proof handy, but it will always give a minimal solution:

```

~ (minimum-scalar-product '(1 3 -5) '(-2 4 1))
 -25

~ (minimum-scalar-product '(1 2 3 4 5) '(1 0 1 0 1))
 6

```

Could be helpful if I ever interview at a <a href="http://google.com" title="Google">company that asks this sort of interview question</a>...