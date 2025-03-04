---
title: Swap list nodes
date: 2013-06-26 14:00:42
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Lists
- Memory
---
It's been rather a while since I've worked out a <a title="Programming Praxis" href="http://programmingpraxis.com/">Programming Praxis</a> problem, but they posted a <a title="Swap list nodes" href="http://programmingpraxis.com/2013/06/25/swap-list-nodes/">new one yesterday</a>, so now seems as good a time as any. The problem is relatively simple:

> Given a linked list, swap the kth node from the head of the list with the kth node from the end of the list.

Since all lists in Scheme are linked lists, that part seems easy enough. To make the problem a little more interesting however, I'm going to work it out in a purely functional manner: no mutation.

<!--more-->

So, let's have at it!

At first, I was interested in trying to do this in a single pass, building up data while recurring down and while back. But that code quickly grew into rather a mess with all sorts of edge cases dealing with things like the kth from the end coming before the kth from the front. So in the end, I abandoned that path in favor of a two pass solution:

* Find pointers to the kth node from the head and the kth from the tail.
* Recur down the list, swapping elements when we get to either points.

One neat trick that we can use[^1] is that the pairs that make up lists in Scheme are distinct memory locations--which means that they are `eq?`.

So how can we use that? Well, for step one, all we have to do is `cdr` down the list until we get to the kth node (either from the head or tail). When we find that node, return the current list. This pointer will be `eq?` to itself during the second iteration rather than using indices. So let's start with that code:

```scheme
; Get pointers to the kth head and the kth tail
(define-values (_ kth-head kth-tail)
  (let loop ([i 1] [ls ls])
    (cond
      [(null? ls)
       (values 1 #f #f)]
      [else
       (define-values (j kth-head kth-tail)
         (loop (+ i 1) (cdr ls)))
       (values
        (+ j 1)
        (if (= i k) ls kth-head)
        (if (= j k) ls kth-tail))])))
```

This is a little more complicated than base Scheme because we're returning multiple values. Essentially, this code (the function `loop`) has the type `(int list -> int list list)` where the arguments are:


* a counter from the front
* the current list pointer


In turn, the return values are:


* a counter from the back
* a pointer to the `kth-head` (once we've found it)
* a pointer to the `kth-tail` (once we've found it)


The beauty of this code comes in the last four lines. Essentially, we're always going to increment the end counter, but the two `if` statements only change the `kth-head` or `kth-tail` if we're at the right value, replacing it with the current list `ls`.

So what can we do with this? Well, this part is much more straight forward:

```scheme
; Recur again, swapping the pointers
(let loop ([ls ls])
  (cond
    [(null? ls)        '()]
    [(eq? ls kth-head) (cons (car kth-tail) (loop (cdr ls)))]
    [(eq? ls kth-tail) (cons (car kth-head) (loop (cdr ls)))]
    [else              (cons (car ls)       (loop (cdr ls)))]))
```

If we're at the end, do nothing. Otherwise, rebuild the list, always recurring on the `cdr` of the list and adding the proper `car`. One thing to note is that the structure of those last three elements looks awfully similar. So theoretically, we could rewrite it so that we only have a single `cons`, `car`, and `(loop (cdr ls))`. That code would look something like this:

```scheme
; Recur again, swapping the pointers
(let loop ([ls ls])
  (cond
    [(null? ls) ls]
    [else
     (cons
      (car 
       (cond
         [(eq? ls kth-head) kth-tail] ; k from head
         [(eq? ls kth-tail) kth-head] ; k from tail
         [else ls]))                  ; everything else
      (loop (cdr ls)))]))
```

Personally, I think it gives up something in terms of readability and (given a decent compiler) they should be essentially equivalent. Still, to each their own. 

With that though, that's all that we need. Just put it all together:

```scheme
; Given a list, swap the kth from head and tail
(define (swap-kth ls k)
  ; Get pointers to the kth head and the kth tail
  ...

  ; Recur again, swapping the pointers
  ...)
```

And it works:

```scheme
> (swap-kth '(1 2 3 4 5) 2)
'(1 4 3 2 5)
```

But does it really work? Well, that's what the `test module` is for:

```scheme
; Make sure that everything works as it should
(module+ test
  (require rackunit)
  (check-equal? (swap-kth '() 3) '())
  (check-equal? (swap-kth '(1) 3) '(1))
  (check-equal? (swap-kth '(1 2) 3) '(1 2))
  (check-equal? (swap-kth '(1 2 3) 3) '(3 2 1))
  (check-equal? (swap-kth '(1 2 3 4) 3) '(1 3 2 4))
  (check-equal? (swap-kth '(1 2 3 4 5) 3) '(1 2 3 4 5))
  (check-equal? (swap-kth '(1 2 3 4 5 6) 3) '(1 2 4 3 5 6))
  (check-equal? (swap-kth '(1 2 3 4 5 6 7) 3) '(1 2 5 4 3 6 7))
  (check-equal? (swap-kth '(1 2 3 4 5 6 7 8) 3) '(1 2 6 4 5 3 7 8))
  (check-equal? (swap-kth '(1 2 3 4 5 6 7 8 9) 3) '(1 2 7 4 5 6 3 8 9)))
```

Run it again... all good. So there you have it. Really, you have all of the pointer swapping ~~power~~ madness that you would have in a language like C, but without the headaches of actually manually managing memory[^2]. 

If you'd like to check out the entire code, you can do so here: 
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/swap-kth.rkt" title="swap kth source on GitHub">swap kth source</a>

[^1]: Which is really the same thing we'd do if we were working in C, just a little nicer looking
[^2]: It's on that list of skills every CS should know, but not something I expect many people actually enjoy doing...