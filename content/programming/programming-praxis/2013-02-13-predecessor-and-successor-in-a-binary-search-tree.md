---
title: Predecessor and successor in a binary search tree
date: 2013-02-13 14:00:53
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Sorting
- Trees
---
<a href="http://programmingpraxis.com/2013/02/12/binary-search-tree-in-order-predecessor-and-successor/" title="Binary Search Tree: In-Order Predecessor And Successor">Yesterday's post</a> from Programming Praxis has us trying to find the predecessor and successor to a given value in a binary search tree. There are actually two general algorithms for doing this, depending on if you have parent pointers or not--but they're asking for the algorithm without.

<!--more-->

The basic idea is that as you recur down the tree looking for a node, you'll also keep track of the last time you branch in each direction (separately). In their examples, they have the code duplicated for each, but I wrote a single function that returns multiple `value`s so that behavior at least is shared.

In any case, the first thing we need to do is set up a `tree` structure:

```scheme
; set up a tree structure
(define-struct tree (value left right) #:transparent)

(define (leaf val) (tree val (empty-tree) (empty-tree)))
(define (leaf? tr) (and (tree? tr) (not (tree-left? tr)) (not (tree-right? tr))))

(define *empty-tree* (tree (void) (void) (void)))
(define (empty-tree) *empty-tree*)
(define (empty? tr) (eq? tr *empty-tree*))

; test if the left node of a tree is non-empty
(define (tree-left? tr)
  (and (tree? tr)
       (not (empty? (tree-left tr)))))

; test if the right node of a tree is non-empty
(define (tree-right? tr)
  (and (tree? tr)
       (not (empty? (tree-right tr)))))
```

Here we have the basic struct along with a few helper functions for making an `empty-tree` and for testing if we have an `empty?` subtree, either left or right.

The next step will be to go ahead and write a function for finding the `minimum` and `maximum` value in a tree. This doesn't actually care at all how the values have been stored, it's just a matter of going left/right until you can't anymore. Here's `minimum`, you can see `maximum` <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/bst-pred%2Bsucc.rkt" title="BST predecessor / successor source">on GitHub</a> (although it's essentially the same).

```scheme
; find the minimum value in a binary search tree
(define (minimum tr)
  (cond
    [(empty? tr) (void)]
    [(tree-left? tr)
     (minimum (tree-left tr))]
    [else
     (tree-value tr)]))
```

Next, the core of the algorithm, we want to be able to find the node containing a value and the last time we went either left or right. Here's all of that in one function:

```scheme
; recur to a value, return:
;   the last time we went left
;   the node containing the search values
;   the last time we went right
(define (find-nodes tr < val)
  (let loop ([tr tr] [last-left (void)] [last-right (void)])
    (cond
      [(empty? tr)
       (values last-left tr last-right)]
      [(equal? val (tree-value tr))
       (values last-left tr last-right)]
      [(< val (tree-value tr))
       (loop (tree-left tr) tr last-right)]
      [else
       (loop (tree-right tr) last-left tr)])))
```

From here, we actually have everything we need to build a `successor` function:

```scheme
; get the successor to a value
(define (successor tr < val)
  (define-values (l v r) (find-nodes tr < val))
  (cond
    [(tree-right? v)
     (minimum (tree-right v))]
    [(and (not (void? l)) (not (empty? l)))
     (tree-value l)]))
```

Basically, we'll get the last left as `l`, the tree containing the value we're looking for as `v`, and the last right as `r`. Then, if we can go right from the value, the `minimum` node there is the successor. If we can't, that means that we went left at some point getting here. Find the most recent left branch (`l`) and find it's value instead.

And that's it. Here's `predecessor` as well:

```scheme
; get the predecessor to a value
(define (predecessor tr < val)
  (define-values (l v r) (find-nodes tr < val))
  (cond
    [(tree-left? v)
     (maximum (tree-left v))]
    [(and (not (void? r)) (not (empty? r)))
     (tree-value r)]))
```

One thing that's interesting about these is that you can actually use them to implement a form of tree sort. Start by finding the `minimum` value. After that, repeatedly find the `successor` until you have all of the values:

```scheme
; sort using a tree, using successor
; this is actually O(n log n) believe it or not
(define (tree-sort < ls)
  (define tr (insert-all (empty-tree) < ls))
  (let loop ([x (minimum tr)])
    (cond
      [(void? x) '()]
      [else
       (cons x (loop (successor tr < x)))])))
```

It's actually still `O(n log n)` (there are `n O(log n)` insertions to build the tree, a `O(log n)` search to find the minimum, and a O(log n) search for each value). I feel like it will have a significantly higher constant than other `O(n log n)` sorts (particularly if the tree isn't well balanced), but it's surprisingly effective (at least experimentally on the same order as quicksort):

```scheme
> (define ls (shuffle (range 1000000)))
> (time (quicksort < ls))
cpu time: 13073 real time: 13113 gc time: 6739
...
> (time (tree-sort < ls))
cpu time: 56426 real time: 56795 gc time: 18085
...
> (time (insertion-sort < ls))
; (Stopped after five minutes)
```

And that's it. It's a bit differently organized than the code that Programming Praxis posted as <a href="http://programmingpraxis.com/2013/02/12/binary-search-tree-in-order-predecessor-and-successor/2/" title="Binary Search Tree: In-Order Predecessor And Successor">their solution</a>, but I think it's still pretty straight forward.

If you'd like to check out the entire source, you can do so on GitHub:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/bst-pred%2Bsucc.rkt">BST predecessor / successor source</a>
