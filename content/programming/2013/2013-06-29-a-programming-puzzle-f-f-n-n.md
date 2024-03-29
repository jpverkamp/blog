---
title: 'A programming puzzle: f(f(n)) = -n'
date: 2013-06-29 14:00:28
programming/languages:
- Racket
- Scheme
programming/topics:
- Mathematics
slug: a-programming-puzzle-ffn-n
---
Two Programming Praxis puzzles in a week? Madness! Let's do it!

<a href="http://programmingpraxis.com/2013/06/28/a-programming-puzzle/">This time</a>, the puzzle at first seems rather minimal:

> Write a function f so that f(f(n)) = -n for all integers n.

If you haven't seen this problem before, take a moment to think though it. It's a neat little problem--a close cousin to a lateral thinking puzzle.

<!--more-->

Okay, time's up. After a bit of thinking, I ended up with basically four ways of solving the puzzle.

The first idea is to realize that the function didn't necessarily specify that `f` only be defined for integers, just that all integers must be negated after two applications. So what sort of mathematical object gives a negative after two applications? Imaginary numbers!

Essentially, we use the fact that {{< inline-latex "i^2 = -1" >}} where {{< inline-latex "i = sqrt(-1)" >}}. So if we multiply by {{< inline-latex "i" >}} once, we get {{< inline-latex "ni" >}}; twice gives us {{< inline-latex "ni^2 = -n" >}}. Perfect:

```scheme
; Rotate in the complex numbers
(define (f1 n)
  (* n 0+1i))
```

That seems a little unfair though, using complex numbers. Can we do it with only integers? 

Of course we can!

To do this, we need to realize that positive/negative is only one axis that splits up the integers. In addition, we could use something like even/odd. This way, we can convert from one to the other (and then back), only applying the negation once. 

Specifically, we'll move all even numbers closer from zero. Any odd numbers, we'll negate then move away from zero. That means we'll only negate once:

```scheme
; Only negate odd numbers, offset by +- 1
(define (f2 n)
  (define e? (even? n))
  (define p? (positive? n))
  (define n? (negative? n))
  (cond
    [(and e? n?) (+ n 1)]
    [(and e? p?) (- n 1)]
    [n?          (+ (- n) 1)]
    [p?          (- (- n) 1)]
    [else        0]))
```

Alternatively, we could get really tricksy and mess with the range/domain of `f` even more (just like the complex numbers). For example, we could cast to a string and back, only negating on the way back:

```scheme
; Wrap as a string, negate on conversion back
(define (f3 n)
  (cond
    [(string? n) (- (string->number n))]
    [else        (number->string n)]))
```

Finally, we can take advantage of the fact that the function will be applied in pairs. So we can add a bit of state to the function. In this example, we create a toggle which is switched on each application of the function. Then, if and only if the toggle is false will we negate the value:

```scheme
; Use a state variable
(define f4
  (let ([toggle (make-parameter #t)])
    (lambda (n)
      (toggle (not (toggle)))
      (if (toggle) n (- n)))))
```

So, do all of these methods work? Well, you could just take my word for it, or you could run some testing. All we care about is double application of integers (single applications and non-integers can return anything), so we'll try to cover the general cases:

```scheme
(module+ test
  (require rackunit)
  (for ([f (in-list (list f1 f2 f3 f4))])
    ; Positive integers
    (for ([i (in-range 10)])
      (define n (random 100))
      (check-equal? (f (f n)) (- n) (format "~s(~s(~s))" f f n)))

    ; Negative integers
    (for ([i (in-range 10)])
      (define n (- (random 100)))
      (check-equal? (f (f n)) (- n) (format "~s(~s(~s))" f f n)))

    ; Zero and +- 1
    (for ([n (in-list '(-1 0 1))])
      (check-equal? (f (f n)) (- n) (format "~s(~s(0))" f f)))))
```

Running this, all is good. Theoretically, we could have missed an edge case, but the functions are simple enough that this seems unlikely. 

If you'd like to check out the full code, you can do so here:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/double-negative.rkt">double negative source on GitHub</a>