---
title: Functions as lists
date: 2013-10-09 14:00:15
programming/languages:
- Lambda Calculus
- Racket
- Scheme
programming/topics:
- Data Structures
- Functional Programming
- Lists
---
<a href="http://programmingpraxis.com/2013/10/08/functional-style-linked-lists/">Yesterday's challenge</a> from Programming Praxis challenges us to rebuild a data structure near and dear to any Lisper's/Schemer's/Racketer's[^1]/functional programmer's heart: lists. The idea presented in <a href="http://programmingpraxis.com/2013/10/08/functional-style-linked-lists/2/">their sample solution</a> uses two element vectors, directly mimicking the general internal structure of Scheme's lists. How about we do something a bit stranger? :smile:

<!--more-->

If you'd like to follow along with the code, I've pushed it as a GitHub Gist here: <a href="https://gist.github.com/jpverkamp/6896457">jpverkamp/6896457</a>. 

The idea is one that was first presented to me in a second year undergraduate programming languages course and really shows the strengths of [[wiki:lambda calculus]]()[^2]. You don't need vectors to build lists--all you need are functions.

To get started, the basic functions that we want are equivalents to `car`/`first`, `cdr`/`rest`, and `cons`/`pair`. If we can build those, the rest will follow. The main obstacle is reversing how we think of lists. Rather than `cons` building lists and `car` and `cdr` taking them apart, `cons` will create a function which knows how to do either. All `car` and `cdr` have to do is tell it which to do. That may sound like black magic, but lets take a look:

```scheme
; Build and take apart lists
>(define pair (λ (a d) (λ (l) (l a d))))
(define first (λ (l) (l (λ (a d) a))))
(define rest (λ (l) (l (λ (a d) d))))
```

So when we have a list, it's actually a function (`l`) expecting another function in turn (of the form `(λ (a d) ...)`. Let's try it out:

```scheme
> (pair 'a 'b)
#<procedure>
> (first (pair 1 2))
1
> (rest (pair 3 4))
4
> (first (rest (pair 5 (pair 6 7))))
6
```

This works just like you would expect it to. Let's do something I generally don't and hand trace that last example. With this many functions flying about, things can get a bit complicated((Not that the trace is terribly better...)):

```scheme
(first (rest (pair 5 (pair 6 7))))
(first (rest (pair 5 ((λ (a d) (λ (l) (l a d))) 6 7))))
(first (rest (pair 5 (λ (l) (l 6 7)))))
(first (rest ((λ (a d) (λ (l) (l a d))) 5 (λ (l) (l 6 7)))))
(first (rest (λ (l) (l 5 (λ (l) (l 6 7))))))
(first ((λ (l) (l (λ (a d) d))) (λ (l) (l 5 (λ (l) (l 6 7))))))
(first ((λ (l) (l 5 (λ (l) (l 6 7)))) (λ (a d) d)))
(first ((λ (a d) d) 5 (λ (l) (l 6 7))))
(first (λ (l) (l 6 7)))
((λ (l) (l (λ (a d) a))) (λ (l) (l 6 7)))
((λ (l) (l 6 7)) (λ (a d) a))
((λ (a d) a) 6 7)
6
```

So it seems to work as planned. What's next?

Well, we want to be able to represent empty lists. One way we could do it is just using some random value as the 'empty list': 

```scheme
; Empty list
(define empty   (gensym))
(define empty?  (λ (l)   (eq? l empty)))
```

This works well enough, but one problem we get is that the empty list (in this case) doesn't look the same as a list. In one case, it's a symbol; in the other, it's a function:

```scheme
> empty
'g30678
> (pair 1 2)
#<procedure>
```

But that's okay. We can actually still do this. All we have to do is add a third value to the list functions. In addition to the first and rest values, we'll insert a flag telling us if the list is empty. Instead of `(λ (a d) ...)`, we'll have `(λ (a d e) ...)`. Something like this:

```scheme
; Empty list
(define empty   (λ (l)   (l 'error 'error #t)))
(define empty?  (λ (l)   (l (λ (a d e) e))))

; Build and take apart lists
(define pair    (λ (a d) (λ (l) (l a d #f))))
(define first   (λ (l)   (l (λ (a d e) a))))
(define rest    (λ (l)   (l (λ (a d e) d))))
```

We could actually raise an error, but at the moment, simply returning the symbol `error` will suffice. Now we can build 'real' lists rather than just pairs:

```scheme
> empty
#<procedure:empty>
> (empty? empty)
#t
> (first empty)
'error
> (pair 1 (pair 2 (pair 3 empty)))
#<procedure>
> (first (rest (pair 1 (pair 2 (pair 3 empty)))))
2
```

And that's actually all we need. Technically, the project wants us to to add functions equivalent to Scheme's `list-ref`, `length`, `reverse`, and `append`. With the four functions we have though, these definitions aren't any different than they would be writing them by hand in Scheme:

```scheme
; Get the nth item of a list
(define nth     
  (λ (l i) 
    (if (zero? i) 
        (first l) 
        (nth (rest l) (- i 1)))))

; Calculate the length of a list
(define length  
  (λ (l)   
    (if (empty? l) 
        0 
        (+ 1 (length (rest l))))))

; Reverse a list
(define reverse 
  (λ (l)
    (let loop ([l l] [acc empty])
      (if (empty? l)
          acc
          (loop (rest l)
                (pair (first l) acc))))))

; Append two lists
(define append  
  (λ (l r) 
    (if (empty? l) 
        r 
        (pair (first l) (append (rest l) r)))))
```

You can do a few tests to make sure that everything works as you would expect, but it's not particularly pleasant given that the structures we're building are rather opaque. So instead, we'll create functions to convert between traditional lists and these functional lists:

```scheme
; Helpers to convert with traditional lists
(define list->flist
  (λ (l)
    (foldl pair empty l)))

(define flist->list
  (λ (l)
    (if (empty? l)
        '()
        (cons (first l) (flist->list (rest l))))))
```

Now we can tests a few things:

```scheme
> (flist->list
   (append
    (pair 1 (pair 2 empty))
    (pair 3 (pair 4 (pair 5 empty)))))
'(1 2 3 4 5)
> (flist->list
   (reverse
    (pair 6 (pair 7 (pair 8 empty)))))
'(8 7 6)
> (length
   (pair 9 (pair 10 (pair 11 (pair 12 empty)))))
4
> (nth
   (pair 13 (pair 14 (pair 15 (pair 16 empty))))
   2)
15
```

Seems to be working well enough. In practice, you'd likely want to test somewhat more thoroughly, but that's good enough for the time being. 

What I really love about this is just how much you can build with just functions. Technically, we don't even need `#f` or numbers in the examples above. Either can be built with just functions in much the same reason. As a bit of a mental exercise, try to implement `if`, `true`, and `false` using only functions[^3]

If you'd like to see the entire code at once, you can see it here: <a href="https://gist.github.com/jpverkamp/6896457">jpverkamp/6896457</a>.

[^1]: Is there a better term?
[^2]: I've never understood why most people refer to it as *the *lambda calculus. Especially when there are so many variations...
[^3]: Hint: There are only so many ways to arrange functions. :smile: