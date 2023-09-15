---
title: Cyclic equality
date: 2013-04-09 14:00:15
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Data Structures
---
In <a title="Cyclic equality on Programming Praxis" href="http://programmingpraxis.com/2013/04/09/cyclic-equality/">today's post</a> from Programming Praxis, the goal is to check if two cyclic lists are equal. So if you have the cycles `↻(1 2 3 4 5)` and `↻(3 4 5 1 2)`, they're equal. Likewise, `↻(1 2 2 1)` and `↻(2 1 1 2)` are equal. But `↻(1 2 3 4)` and `↻(1 2 3 5)` are not since they have different elements while `↻(1 1 1)` and `↻(1 1 1 1)` aren't since they have different elements.

<!--more-->

Basically, there are two ways that you can solve this problem. First, you actually use the cyclic structure and recursively check each start in one list for a matching cycle in the other. Alternatively, so long as the lengths are equal you can just double one list and search for the other as a subset. We'll go ahead and code up both.

First, we want to write a semi-straight forward comparison. The function will take two lists. It will recur across each in both for a start and loop in the second until either a match is confirmed or not. One thing that I want to do is make a cycle structure. We could use mutation to set the last `cdr`/`tail` of the list to the head, but instead I'll make the following structure:

```scheme
; Store a cycle as the current head and original (reset) head
(define-struct cycle (current original))

; Convert a list to a cycle
(define (list->cycle ls)
  (make-cycle ls ls))

; Convert a cycle to a list
(define (cycle->list c)
  (cycle-take (cycle-length c) c))

; Return the first item of a cycle
(define (cycle-head c)
  (if (null? (cycle-current c))
      (car (cycle-original c))
      (car (cycle-current c))))

; Return all but the first item of a cycle
(define (cycle-tail c)
  (if (null? (cycle-current c))
      (make-cycle (cdr (cycle-original c)) (cycle-original c))
      (make-cycle (cdr (cycle-current c)) (cycle-original c))))

; Get the length of a cycle
(define (cycle-length c)
  (length (cycle-original c)))

; Take the first n items from a cycle
(define (cycle-take n c)
  (let loop ([i 0] [c c])
    (if (= i n)
        '()
        (cons (cycle-head c) (loop (+ i 1) (cycle-tail c))))))

; Test if a cycle is about to reset
(define (cycle-reset? c)
  (null? (cycle-current c)))
```

Essentially, we'll keep a pointer to the original list and reset when the current pointer runs out. All of this is of course transparent to anyone using the API, so we could switch it out for another (using a vector and a current pointer for example) if we wanted. The most useful function yet potentially non-standard function is `cycle-reset?`. Essentially, it fills what would have been `cycle-null?`, except a cycle will never be null. This tests when we're about to reset to the beginning of the cycle.

There are a bunch of unit tests in the <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/cycle-equality.rkt" title="cycle equality source on GitHub">source on GitHub</a>, but reset assured it works.

Now that we have that, the function it relatively straight forward:

```scheme
; Test if two cycles are equal
(define (cycle-equal? c1 c2)
  ; Check the lengths first
  (define len (cycle-length c1))
  (and (= len (cycle-length c2))
       (let loop ([ci1 c1] [ci2 c2])
         (cond
           ; No matches found
           [(cycle-reset? ci1)
            #f]
           ; No match found for this start in c1
           ; Advance c1, reset c2
           [(cycle-reset? ci2)
            (loop (cycle-tail ci1) c2)]
           ; Match found at the current element!
           [(equal? (cycle-take len ci1)
                    (cycle-take len ci2))
            #t]
           ; Otherwise, no match, advance c2
           [else
            (loop ci1 (cycle-tail ci2))]))))
```

Theoretically, the comments should be pretty straight forward. For each starting pair, test if we have matching cycles using `cycle-take`. That could bail out early to make the code more efficient, but at the cost of being rather less clean. Really, if you wanted to make this code efficient you'd most likely use a vector and a head pointer anyways.

And here we have a few tests:

```scheme
> (cycle-equal? (list->cycle '(1 2 3 4 5)) (list->cycle '(1 2 3 4 5)))
#t
> (cycle-equal? (list->cycle '(1 2 3 4 5)) (list->cycle '(3 4 5 1 2)))
#t
> (cycle-equal? (list->cycle '(1 2 2 1)) (list->cycle '(2 1 1 2)))
#t
> (cycle-equal? (list->cycle '(1 1)) (list->cycle '(1 1 1 1)))
#f
> (cycle-equal? (list->cycle '(1 2 3 4)) (list->cycle '(1 2 3 5)))
#f
```

The next solution is a bit more straight forward if not quite as efficient. Essentially, double one of the lists and then check if the other is in it. For equal cycles, this will be equal but not others. You do have to check the length first though.

First, we need to write code to check if one given list is a subset anywhere in another. Here's one way to do that:

```scheme
; Check if p is a prefix of ls
(define (prefix? ls p)
  (or (null? p)
      (and (equal? (car ls) (car p))
           (prefix? (cdr ls) (cdr p)))))

; Check if a list needle is in the list haystack
(define (contains? haystack needle)
  (and (not (null? haystack))
       (or (prefix? haystack needle)
           (contains? (cdr haystack) needle))))
```

And with that, checking for equal is a rather minimal function (we're taking the cycles as lists this time):

```scheme
; Check if two cycles (as lists) are equal by doubling one
(define (list-cycle-equal? lsc1 lsc2)
  (and (= (length lsc1) (length lsc2))
       (contains? (append lsc1 lsc1) lsc2)))
```

And to check that we can use the same tests. We just don't convert to cycles first:

```scheme
> (list-cycle-equal? '(1 2 3 4 5) '(1 2 3 4 5))
#t
> (list-cycle-equal? '(1 2 3 4 5) '(3 4 5 1 2))
#t
> (list-cycle-equal? '(1 2 2 1) '(2 1 1 2))
#t
> (list-cycle-equal? '(1 1) '(1 1 1 1))
#f
> (list-cycle-equal? '(1 2 3 4) '(1 2 3 5))
#f
```

And that's it. If you'd like, you can see the entire code on GitHub (<a href="https://github.com/jpverkamp/small-projects/blob/master/blog/cycle-equality.rkt" title="cycle equality source on GitHub">cycle equality source</a>). All of the functions are already in this post, but there are a bunch of unit tests that might be of interest.

**Edit 9 April 2013**: A comment from Maurits on the Programming Praxis post got me wondering if it could be done in *O(m + n)*[^1]. Basically, their idea was to lexically order both cycles and then check if they are equal as lists.

To lexically order them, we want to advance the cycle so that the smallest element in the cycle is first. If there is a tie, break it with the element right after each smallest and so on. Something like this:

```scheme
; Advance a cycle to the lexically minimum position
(define (cycle-lexical-min c [< <] [= =])
  ; Check if one cycle is less than another
  (define (cycle-< c1 c2)
    (let loop ([c1 c1] [c1-cnt (cycle-length c1)]
               [c2 c2] [c2-cnt (cycle-length c2)])
      (and (> c1-cnt 0)
           (> c2-cnt 0)
           (or (< (cycle-head c1) (cycle-head c2))
               (and (= (cycle-head c1) (cycle-head c2))
                    (loop (cycle-tail c1) (- c1-cnt 1)
                          (cycle-tail c2) (- c2-cnt 1)))))))

  ; Lexically sort by storing minimum
  (let loop ([min c] [c (cycle-tail c)])
    (cond
      [(cycle-reset? c) min]
      [(cycle-< c min) (loop c (cycle-tail c))]
      [else (loop min (cycle-tail c))])))
```

Note: This code uses an updated version of `cycle-length` that is [[wiki:amortized]]() *O(1)* (it caches the length). You can see the code for that on <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/cycle-equality.rkt" title="cycle equality source on GitHub">GitHub</a>. 

One you have the sort, the actual comparison is easy:

```scheme
; Compare cycles by lexical comparison
(define (lexical-cycle-equal? c1 c2 [< <] [= =])
  (equal? (cycle-take (cycle-length c1) (cycle-lexical-min c1 < =))
          (cycle-take (cycle-length c2) (cycle-lexical-min c2 < =))))
```

I’m not completely sure about the runtime of finding the lexical minimum. In the general case (with few duplicates), it’ll be *O(n)* though. Then there’s another *O(n + n)* for the cycle-length and cycle-take, plus a final additional *O(max(m, n))* for the equal?. So overall it would be *O(3m + 3n + max(m, n))* which is *O(m + n)*. The constant could be improved with a better abstraction, but not the big-O time.

And of course all of the previous tests still work:

```scheme
> (lexical-cycle-equal? (list->cycle '(1 2 3 4 5)) (list->cycle '(1 2 3 4 5)) < =)
#t
> (lexical-cycle-equal? (list->cycle '(1 2 3 4 5)) (list->cycle '(3 4 5 1 2)) < =)
#t
> (lexical-cycle-equal? (list->cycle '(1 2 2 1)) (list->cycle '(2 1 1 2)) < =)
#t
> (lexical-cycle-equal? (list->cycle '(1 1)) (list->cycle '(1 1 1 1)) < =)
#f
> (lexical-cycle-equal? (list->cycle '(1 2 3 4)) (list->cycle '(1 2 3 5)) < =)
#f
```

[^1]: The previous two solutions are *O(mn)* because they have to compare each starting point pairwise