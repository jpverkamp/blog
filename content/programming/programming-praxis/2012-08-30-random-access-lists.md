---
title: Random Access Lists
date: 2012-08-30 14:00:28
programming/languages:
- Scheme
programming/sources:
- Programming Praxis
---
This time around, Programming Praxis [here](https://github.com/jpverkamp/small-projects/blob/master/blog/ralist.ss) (make sure you download pmatch as well).

First, we need to provide tree functions that are designed to work on complete {{< wikipedia "binary trees" >}}, taking the size as an additional parameters. 

```scheme
; lookup an item in a balanced binary tree
(define (tree-lookup size tr i)
  (pmatch (list size tr i)
    [(,size (Leaf ,x) 0)
     x]
    [(,size (Leaf ,x) ,i)
     (error 'tree-lookup "subscript-error")]
    [(,size (Node ,x ,t1 ,t2) 0)
     x]
    [(,size (Node ,x ,t1 ,t2) ,i)
     (let ([size^ (div size 2)])
       (if (<= i size^)
           (tree-lookup size^ t1 (- i 1))
           (tree-lookup size^ t2 (- i 1 size^))))]))

; update a balanced binary tree with a new element
(define (tree-update size tr i y)
  (pmatch (list size tr i y)
    [(,size (Leaf ,x) 0 ,y) 
     `(Leaf ,y)]
    [(,size (Leaf ,x) ,i ,y) 
     (error 'tree-update "subscript error")]
    [(,size (Node ,x ,t1 ,t2) 0 ,y)
     `(Node ,y ,t1 ,t2)]
    [(,size (Node ,x ,t1 ,t2) ,i ,y)
     (let ([size^ (div size 2)])
       (if (<= i size^)
           `(Node ,x ,(tree-update size^ t1 (- i 1) y) ,t2)
           `(Node ,x ,t1 ,(tree-update size^ t2 (- i 1 size^) y))))]))
```

With that, we have everything we need to represent the lists. A random access list will be defined as follows:

```
ralist := empty
       || (size tree) :: ralist
```

Using that definition (and Scheme's standard empty lists for the empty ralist as well), `null?` is each enough to define:

```scheme
(define (*null? ra)
  (null? ra))
```

`cons` is a little more interesting as we have to deal with potentially merging the first two items in the list to preserve the `O(log(n))` access to the list. It's still `O(1)` overall for the cons though. Here's where the power of pattern matching really shines though. 

```scheme
; build a random access list
(define (*cons x xs)
  (pmatch xs
    [((,size1 ,t1) (,size2 ,t2) . ,rest)
     (if (= size1 size2)
         `((,(+ 1 size1 size2) (Node ,x ,t1 ,t2)) . ,rest)
         `((1 (Leaf ,x)) . ,xs))]
    [else
     `((1 (Leaf ,x)) . ,xs)]))
```

`car` and `cdr` (they were named `head` and `tail` in the original paper which really makes more sense, but I wanted to keep to the Scheme naming convention) aren't bad at all, the only interesting part is taking the `cdr` of a list will split the first tree. 

```scheme
; return the first item in a random access list
; head in the paper
(define (*car ls)
  (pmatch ls
    [() (error '*car "empty list")]
    [((,size (Leaf ,x)) . ,rest) 
     x]
    [((,size (Node ,x ,t1 ,t2)) . ,rest)
     x]))

; return all but the first item of a random access list
; tail in the paper
(define (*cdr ls)
  (pmatch ls
    [() (error '*cdr "empty list")]
    [((,size (Leaf ,x)) . ,rest) 
     rest]
    [((,size (Node ,x ,t1 ,t2)) . ,rest)
     (let ([size^ (div size 2)])
       `((,size^ ,t1) (size^ ,t2) . ,rest))]))
```

The last functions presented in the paper are `lookup` and `update`, which have been given their Scheme names of `list-ref` and `list-set` (note: not `list-set!` since the update is purely functional and no mutation is occurring). Again, very straight forward.

```scheme
; pull an item out of the list in O(log(n)) time
; lookup in the paper
(define (*list-ref ls i)
  (pmatch (list ls i)
    [(() ,i)
     (error '*list-ref "subscript error")]
    [(((,size ,t) . ,rest) ,i)
     (if (< i size)
         (tree-lookup size t i)
         (*list-ref rest (- i size)))]))

; return a new random access list with one specified change
; update in the paper
(define (*list-set ls i y)
  (pmatch (list ls i y)
    [(((,size ,t) . ,rest) ,i ,y)
     (if (< i size)
         `((,size ,(tree-update size t i y)) . ,rest)
         `((,size ,t) . ,(*list-set rest (- i size) y)))]))
```

Here are a few examples of running the code that should show you that it functions identically to Scheme's standard list functions (except `list-ref` is faster!).

```scheme
~ (*cons 'a '())
 ((1 (leaf a)))

~ (*car (*cons 'a 'b))
 a

~ (*cdr (*cons 'a 'b))
 b

~ (define *ls (*cons 'a (*cons 'b (*cons 'c (*cons 'd (*cons 'e '()))))))

~ *ls
 ((1 (leaf a)) (1 (leaf b)) (3 (node c (leaf d) (leaf e))))

~ (*car (*cdr (*cdr *ls)))
 c

~ (*list-ref *ls 2)
 c

~ (*list-ref *ls 4)
 e

~ (*list-set *ls 3 'frog)
 ((1 (leaf a))
  (1 (leaf b))
  (3 (node c (leaf frog) (leaf e))))

~ (define *ls2 (*list-set *ls 3 'frog))

~ (*list-ref *ls2 3)
 frog

~ (equal? *ls *ls2)
 #f
```

[Here's](https://github.com/jpverkamp/small-projects/blob/master/blog/ralist.ss) all of the code together (don't forget pmatch as well).