---
title: Splay heaps redux-imperative model
date: 2013-01-24 14:00:32
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Data Structures
- Sorting
---
I did say in [yesterday's comments]({{< ref "2013-01-23-sorting-via-splay-heap.md" >}}) that I would try re-implementing splay heaps using an imperative model with an array (Scheme's `vector`) as the back end rather than a functional one with trees. Well, here is is.

<!--more-->

The first change is an obvious one. We need a new data structure (if you'd like, you can follow along <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/splay-heap-array.rkt" title="Splay heap on GitHub">here</a>):

```scheme
; wrap a heap in a struct
(define-struct heap (data size <) 
  #:transparent
  #:mutable)
```

`data` is a vector which we'll occasionally have to rebuilt, `size` is the number of elements stored in the vector (not necessarily the size of the vector), and `<` is the comparator. This time, we need to make sure that the structure is `mutable` so we get functions like `set-heap-data!` and friends. 

The next thing we need is a helper function to grow the internal vector. Since Scheme vectors have a static size, each time we outgrow it we need to create a new larger vector and copy over the old values. Taking a page from the <a href="http://hg.openjdk.java.net/jdk6/jdk6-gate/jdk/file/b139627f7bc3/src/share/classes/java/util/PriorityQueue.java" title="OpenJDK PriorityQueue">OpenJDK implementation of a PriorityQueue</a>, we will double the internal vector size each time up until we reach 64 and only grow by 150% after that. Here's the function for that.

```scheme
; grow a heap
; if it's small, double in size; otherwise 1.5x
(define (grow! heap)
  (define old-size (heap-size heap))
  (define new-size (* old-size (if (< old-size 64) 2 3/2)))
  (set-heap-data!
   heap
   (for/vector ([i (in-range new-size)])
     (and (< i old-size)
          (vector-ref (heap-data heap) i)))))
```

Next, we'd want to work on `push!` (which was previously `insert`), but before that, we need two more helper functions: `shift-up!` and `shift-down!`. The basic idea is that even if we're using a vector, it still has the structure of a tree. Instead of inexplicably storing the relationships though, we store the children at indices *2n+1* and *2n+2*. For example, this tree is equivalent to this array:

```scheme
0
   /   \
  1     2
 / \   /
3   4 5
```


| 0 | 1 = parent | 2 | 3 = left | 4 = right | 5 |
|---|------------|---|----------|-----------|---|


To be a heap, we need the property that each value in the heap is less than either of its two children (recursively). So the example above is also a valid heap. `sift-up!` and `sift-down!` are how we will maintain that relationship when inserting or removing an element.

First, `sift-up!`. `sift-up!` will start at the bottom of the tree. In the example above, we would insert a new element where the 6 would be. We then repeatedly exchange the node with its parent until it's smaller. The rest of the heap does not need to be altered. Say we are adding the value -1 to the tree:

```scheme
0
   /   \
  1     2
 / \   / \
3   4 5  -1

     0
   /   \
  1    -1
 / \   / \
3   4 5   2

    -1
   /   \
  1     0
 / \   / \
3   4 5   2
```

In Racket terms, we have:

```scheme
; re-sift the heap upwards
(define (sift-up! heap index value)
  (define parent (arithmetic-shift (+ -1 index) -1))
  (cond
    ; at the top, we have to stop here
    ; or the parent is already smaller
    [(or (= index 0)
         (not ((heap-< heap) value (vector-ref (heap-data heap) parent))))
     (vector-set! (heap-data heap) index value)]
    ; otherwise sift, move the parent down and recur
    [else
     (vector-set! (heap-data heap) 
                  index 
                  (vector-ref (heap-data heap) parent))
     (sift-up! heap parent value)]))
```

There was actually a rather sneaky bug in this function that haunted me right up until the end. It only rarely manifested itself, but broke all sorts of things. Curses for off by one errors!

In any case, the next function is the inverse of `shift-up!`--`shift-down!`. This time, we start at the top of the tree and exchange with the smaller node that's still larger than the new value. Here's an example (using the actual algorithm for `pop!` where the root is replaced with the last value in the array):

```scheme
2
   /   \
  1     0
 / \   /
3   4 5 

     0
   /   \
  1     2
 / \   / 
3   4 5
```

There are a few sneakier parts of the algorithm, but I finally managed to work it all out:

```scheme
; re-sift the heap downwards
(define (sift-down! heap index value)

  (define left (+ 1 (arithmetic-shift index 1)))
  (define right (+ 1 left))

  (cond
    ; we're out in the branches or smaller than children
    [(and (or (>= left (heap-size heap))
              ((heap-= right (heap-size heap))
              ((heap-= right (heap-size heap))
              ((heap-< heap) value (vector-ref (heap-data heap) left)))
         ((heap-< heap) (vector-ref (heap-data heap) left)
                        (vector-ref (heap-data heap) right)))
     (vector-set! (heap-data heap)
                  index
                  (vector-ref (heap-data heap) left))
     (sift-down! heap left value)]
    ; otherwise, recur to the right
    [else
     (vector-set! (heap-data heap)
                  index
                  (vector-ref (heap-data heap) right))
     (sift-down! heap right value)]))
```

It's still not completely clean, but this is the most complicated function in the new version and I think it's still a bit easier to read than the functional version from yesterday. Perhaps that's just me though. 

Now that we have both shifting functions, we can easily write `push!`:

```scheme
; insert an item into a heap
(define (push! heap value)
  (when (= (heap-size heap) (vector-length (heap-data heap)))
    (grow! heap))

  (define size (heap-size heap))
  (set-heap-size! heap (+ 1 size))

  (if (= 1 (heap-size heap))
      (vector-set! (heap-data heap) 0 value)
      (sift-up! heap size value)))
```

It's a simple matter of growing the heap if necessary and shifting the element downwards from the top. That way we have the new item and the heap's properties are maintained.

Likewise, we have enough to write the inverse function `pop!`:

```scheme
; pop! the minimum element in a heap (and return it)
(define (pop! heap)
  (when (= 0 (heap-size heap))
    (error 'pop! "empty heap"))

  (define result (peek heap))
  (define last (vector-ref (heap-data heap) (+ -1 (heap-size heap))))

  (set-heap-size! heap (+ -1 (heap-size heap)))
  (unless (zero? (heap-size heap))
    (sift-down! heap 0 last))
  (vector-set! (heap-data heap) (heap-size heap) #f)

  result)
```

Like I mentioned earlier, the algorithm is to pull off the smallest item. After that's been done, the last item in the array (the rightmost on the lowest layer of the tree) is put at the top and it gets sifted back downwards until the heap is fixed. Because nothing other than one path down the tree is modified either way, that means that both `push!` and `pop!` have O(log n) runtime.

And that's (almost) actually everything. The `heapsort` function has to be modified slightly in order to account for the functional algorithm, but that's an easy enough change:

```scheme
; sort a list using a heap
(define (heapsort ls <)
  (define heap (new-heap <))

  (let loop ([ls ls])
    (unless (null? ls)
      (push! heap (car ls))
      (loop (cdr ls))))

  (let loop ()
    (if (empty? heap)
        &#039;()
        (cons (pop! heap) (loop)))))
```

Test it with the same code as last time:

```scheme
; randomized testing
(require rackunit)
(for ([i (in-range 100)])
  (define ls (for/list ([i 20]) (random 100)))
  (check-equal? (heapsort ls <) (sort ls <)))
```

Everything works out well enough. It took a while to track down said earlier sneaky error (I thought it was in `shift-down!` but it was actually in `shift-up!`), but it was an interesting exercise to see how different it was.

If you'd like to download today's code, you can do so here: 
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/splay-heap-array.rkt" title="Splay heap on GitHub">splay heap source</a>