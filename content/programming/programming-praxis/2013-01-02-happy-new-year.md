---
title: Happy New Year
date: 2013-01-02 14:00:40
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Mathematics
---
<a title="Happy New Year!" href="http://programmingpraxis.com/2013/01/01/happy-new-year/">Yesterday's post</a> from Programming Praxis asks us to build a very special sort of expression. Using the numbers 10, 9, 8, 7, 6, 5, 4, 3, 2, and 1 in that order along with the operators of multiplication, division, addition, subtraction, and concatenation, find all of the ways that we can write an expression totaling 2013. Here's one valid solution:

{{< latex >}}109 - 8 * 7 + 654 * 3 - 2 / 1 = 2013{{< /latex >}}

<!--more-->

Since I'm going to be working in Racket, the first thing that we need is a program that can evaluate an infix expression. I'm actually going to make the program far more general, able to use any combination of binary operators with any given precedence levels. It's similar to what I wrote quite a while ago about [evaluating infix expressions]({{< ref "2012-10-08-evaluating-prefix-infix-postfix-expressions.md" >}}), but the code is a little different, so I'll post it here as well.

First, we need a function that can reduce an expression using all of the operators with the same precedence. Given an expression as a list and a list of pairs of operator names and functions, you can do it like this:

```scheme
; reduce one level 
(define (reduce expr ops)
  (cond
    [(or (null? expr)
         (null? (cdr expr))
         (null? (cddr expr)))
     expr]
    [(assoc (cadr expr) ops)
     => (lambda (pair)
          (reduce (cons ((cadr pair) (car expr) (caddr expr)) (cdddr expr)) ops))]
    [else
     (cons (car expr) (reduce (cdr expr) ops))]))
```

The first part means that we don't reduce if we're too close to the end of the expression. The `assoc` on the second part along with the `=>` syntax means that we can find the first matching symbol in the operator list and apply it. If this doesn't work, the `else` will skip along.

After that, we need a driver that can call this with each level of operator: 

```scheme
; step through each level of ops
(define (step expr ops)
  (cond
    [(null? ops)
     expr]
    [else
     (step (reduce expr (car ops)) (cdr ops))]))
```

Pretty straight forward recursion there. The only potentially confusing bit is that the variable `ops` means different things depending on which function you're dealing with. 

Finally, combine those together:

```scheme
; evaulate an infix expression given a list of ops
; ops is a list of pairs of symbol -> binary function
; example: (((* *) (/ div))
;           ((+ +) (- -)))
(define (evaluate expr ops)
  ; step through each level of ops
  (define (step expr ops)
    ...)

  ; reduce one level 
  (define (reduce expr ops)
    ...)

  ; start out the main loop
  (car (step expr ops)))
```

And test it out:

```scheme
> (evaluate '(10 ~ 9 - 8 * 7 + 6 ~ 5 ~ 4 * 3 - 2 / 1)
            `(((~ ,(lambda (x y) 
                     (string->number (string-append 
                                      (number->string x) 
                                      (number->string y))))))
              ((* ,*) (/ ,/))
              ((+ ,+) (- ,-))))
2013
```

So far, so good. So how about generating all of the possible expressions? This is a straight forward use of Racket's `for` macro to generate append each operator in turn onto the list of numbers. In this case, the list of operators is just a list of symbols.

```scheme
; generate a list of expressions given an ordered list
; of values and a list of possible operations between
; them
(define (generate nums ops)
  (cond
    [(null? (cdr nums))
     (list nums)]
    [else
     (for*/list ([op (in-list ops)]
                 [res (in-list (generate (cdr nums) ops))])
       (list* (car nums) op res))]))
```

Test it out (on a much smaller example, the full example has about 2 million possibilities):

```scheme
> (generate '(3 2 1) '(+ -))
'((3 + 2 + 1) (3 + 2 - 1) (3 - 2 + 1) (3 - 2 - 1))
```

Now, we have all of the pieces we need to tie everything together:

```scheme
; given an ordered list of numbers, a list of ops on
; them, and a target return all interspaced lists that
; evaluate to the given target
(define (solve nums ops target)
  (for ([expr (in-list (generate nums (map car (apply append ops))))]
        #:when (= (evaluate expr ops) target))
    (printf "~s\n" expr)))
```

So we just generate each expression and test it against the target. If we're looking for 10, 9, 8, 7, 6, 5, 4, 3, 2, 1 with the four standard operators plus concatenation and all working out to 2013, we want this:

```scheme
> (solve '(10 9 8 7 6 5 4 3 2 1)
         `(((~ ,(lambda (x y)
                  (string->number (string-append 
                                   (number->string x)
                                   (number->string y))))))
           ((* ,*) (/ ,/))
           ((+ ,+) (- ,-)))
         2013)
(10 ~ 9 - 8 * 7 + 6 ~ 5 ~ 4 * 3 - 2 * 1)
(10 ~ 9 - 8 * 7 + 6 ~ 5 ~ 4 * 3 - 2 / 1)
(10 * 9 ~ 8 / 7 * 6 / 5 * 4 * 3 - 2 - 1)
(10 * 9 * 8 * 7 / 6 / 5 * 4 * 3 - 2 - 1)
```

And there you have it. The four ways to write the expected expressions:

{{< latex >}}109 - 8 * 7 + 654 * 3 - 2 * 1 = 2013{{< /latex >}}

{{< inline-latex "109 - 8 * 7 + 654 * 3 - 2 / 1 = 2013" >}}

{{< latex >}}10 * 98 / 7 * 6 / 5 * 4 * 3 - 2 - 1 = 2013{{< /latex >}}

{{< inline-latex "10 * 9 * 8 * 7 / 6 / 5 * 4 * 3 - 2 - 1 = 2013" >}}

It took about 20 seconds to run, which is slower than it could be (considering that I'm evaluating the infix expressions myself and generating all of the possible solutions in memory at once), but it's well within a minute, so it's good enough. 

If you'd like to download the source for today's post, you can do so here:
- <a href="Happy New Year source on GitHub">happy-new-years.rkt</a>