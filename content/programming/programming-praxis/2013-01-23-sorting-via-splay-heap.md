---
title: Sorting via splay heap
date: 2013-01-23 14:00:32
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Data Structures
- Sorting
---
<a href="http://programmingpraxis.com/2013/01/22/splay-heaps/" title="Splay Heap">Yesterday's post</a> from Programming Praxis gives a new (or at least different) vantage point on one of the most common problems in Computer Science: sorting. Today, we're going to implement a data structure known as a {{< wikipedia "splay heap" >}} and use that to perform a {{< wikipedia "heapsort" >}}.

<!--more-->

This was actually pretty complicated to get working, mostly as there are so many details to get right that are a bit rough in a functional language. Generally, heaps are implemented using a mutable array, flipping values as necessary. But where's the fun in that?

If you'd like to follow along, you can download the full source <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/splay-heap.rkt" title="Splay heap source on GitHub">here</a>. Essentially, there are three functions that we want to write: `insert`, `first`, and `rest`.

So how does it look?

Well, first we need a few structures. We're going to use a `node` structure for the tree and a `heap` structure to wrap it all up, including the comparator:

```scheme
; splay heap nodes
(define-struct node (value left right) #:transparent)

(define empty-node (node (void) #f #f))
(define (empty-node? node) (and (node? node) (void? (node-value node))))

; the entire heap, store comparator
(define-struct heap (root <) #:transparent)
```

Good to go. There's one unfortunate aspect in that we want to export `make-hash`, but we only want to specify the comparator. That's not too bad though, we can do that with `provide` and `rename-out`.

Next, we want to start with the hardest bit of code: inserting a new value into the heap.

To `insert`, the basic idea is to recursively partition the tree (in a manner similar to {{< wikipedia "quicksort" >}}) into a subtree with items smaller than the new value and a subtree larger. The trick though is when you go left twice (towards the smallest nodes, which we want to access quickly) you want to rotate the tree to make that lookup quicker. This will give us an {{< wikipedia page="Amortized analysis" text="amortized runtime" >}} (the runtime over many repeated runs of the algorithm) of O(n log n), on the same order as the other best sorting algorithms ({{< wikipedia "quicksort" >}} / {{< wikipedia "mergesort" >}}).

```scheme
; insert a value into a splay heap
(define (insert heap pivot)
  (define < (heap-< heap))

  ; split a node into a tree of < nodes and non < nodes
  (define (partition node)
    (cond
      ; no values
      [(empty-node? node)
       (values empty-node empty-node)]
      ; new node will go left
      [(< pivot (node-value node))
       (cond
         ; and there&#039;s nothing the other way
         [(empty-node? (node-left node))
          (values empty-node node)]
         ; right than right
         [(< pivot (node-value (node-left node)))
          (define-values (left right)
            (partition (node-left (node-left node))))
          (values left
                  (make-node (node-value (node-left node))
                             right
                             (make-node (node-value node)
                                        (node-right (node-left node))
                                        (node-right node))))]
         ; right then left
         [else
          (define-values (left right)
            (partition (node-right (node-left node))))
          (values (make-node (node-value (node-left node))
                             (node-left (node-left node))
                             left)
                  (make-node (node-value node)
                             right
                             (node-right node)))])]
      ; new node will go right
      [else
       (cond
         ; and there&#039;s nothing there
         [(empty-node? (node-right node))
          (values node empty-node)]
         ; right than right
         [(< pivot (node-value (node-right node)))
          (define-values (left right)
            (partition (node-left (node-right node))))
          (values (make-node (node-value node)
                             (node-left node)
                             left)
                  (make-node (node-value (node-right node))
                             right
                             (node-right (node-right node))))]
         ; right than left
         ; this is the rotation case
         [else
          (define-values (left right)
            (partition (node-right (node-right node))))
          (values (make-node (node-value (node-right node))
                             (make-node (node-value node)
                                        (node-left node)
                                        (node-left (node-right node)))
                             left)
                  right)])]))

  ; insert the node
  (define-values (left right)
    (partition (heap-root heap)))

  (make-heap (make-node pivot left right) <))
```

That's a fair bit of code, but hopefully it's commented well enough to follow. In the inner define (that actual `partition` function), we're returning two `value`s: a heap of smaller values and a heap of larger values. The most interesting case of that is the left than left case where the rotation I mentioned earlier takes place.

Moving on, we have the `first` and `rest` functions. We'll start with `first`. Since we know the heap (and each sub-heap by extension) has all smaller values down the left side, we just have to keep recurring left until we can't anymore. That will be the minimum value. And since we're not actually changing anything, the code is straight forward:

```scheme
; get the smallest node from the heap
(define (first heap)
  (let loop ([node (heap-root heap)])
    (cond
      [(empty-node? node)
       (error 'first "empty heap")]
      [(empty-node? (node-left node))
       (node-value node)]
      [else
       (loop (node-left node))])))
```

Finally, what do we need to do to get everything but the minimum value?

```scheme
; get the heap without the smallest node
(define (rest heap)
  (make-heap
   (let loop ([node (heap-root heap)])
     (cond
       [(empty-node? node)
        (error 'rest "empty heap")]
       [(empty-node? (node-left node))
        (node-right node)]
       [(empty-node? (node-left (node-left node)))
        (make-node (node-value node)
                   (node-right (node-left node))
                   (node-right node))]
       ; left than left
       ; this is the rotation case
       [else
        (make-node (node-value (node-left node))
                   (loop (node-left (node-left node)))
                   (make-node (node-value node)
                              (node-right (node-left node))
                              (node-right node)))]))
```

Now we need to test it to make sure everything is working. How else, but to write the actual `heapsort` code. Essentially, insert each item into a heap in turn, then pull each back out. Because of the {{< wikipedia page="Amortized analysis" text="amortized runtime" >}}, this should be fast.

```scheme
; sort using a heap
(define (heapsort ls <)
  (let loop ([ls ls] [heap (make-heap empty-node <)])
    (if (null? ls)
        (let loop ([heap heap])
          (if (empty? heap)
              &#039;()
              (cons (first heap) (loop (rest heap)))))
        (loop (cdr ls) (insert heap (car ls))))))
```

And testing it out:

```scheme
; randomized testing
(require rackunit)
(for ([i (in-range 100)])
  (define ls (for/list ([i 20]) (random 100)))
  (check-equal? (heapsort ls <) (sort ls <)))
```

Everything succeeds. You can easily test it with other comparison functions and random data sources, but there's no reason that it shouldn't work. 

And there you have it. Personally, I'm not sure why you'd actually use such a data structure, particularly since other sorting algorithms are just as fast and easier to implement in a functional environment. But perhaps there is a case I just haven't seen yet. 

If you'd like to download today's source code, you can do so here:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/splay-heap.rkt" title="Splay heap source on GitHub">splay heap</a>