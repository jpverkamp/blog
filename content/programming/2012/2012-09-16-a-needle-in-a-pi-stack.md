---
title: A needle in a Pi-stack
date: 2012-09-16 14:00:02
programming/languages:
- Racket
- Scheme
---
Recently I've been watching a lot of [find-in-pi source code](https://github.com/jpverkamp/small-projects/blob/master/blog/find-in-pi.rkt)

```scheme
(require racket/generator)

(define (make-pi-spigot)
  (generator ()
    (let loop ([q 1] [r 0] [t 1] [k 1] [n 3] [l 3])
      (if (< (- (+ (* 4 q) r) t) (* n t))
          (begin
            (yield n)
            (loop (* 10 q)
                  (* 10 (- r (* n t)))
                  t
                  k
                  (- (quotient (* 10 (+ (* 3 q) r)) t) (* 10 n))
                  l))
          (loop (* q k)
                (* (+ (* 2 q) r) l)
                (* t l)
                (+ k 1)
                (quotient (+ (* q (+ (* 7 k) 2)) (* r l)) (* t l))
                (+ l 2))))))
```

Simple enough to use, we can use Racket's {{< doc racket "for" >}} to generate a list of n digits of pi or to convert the same to a string:

```scheme
(define (digits-of-pi n)
  (for/list ([i (in-range (+ n 1))]
             [d (in-producer (make-pi-spigot) #f)])
    d))

(define (pi->string n)
  (string-append
   "3."
   (apply
    string-append
    (map number->string (cdr (digits-of-pi n))))))

> (digits-of-pi 10)
'(3 1 4 1 5 9 2 6 5 3 5)

> (pi->string 10)
"3.1415926535"
```

In any case, it seems to be working well enough so far, so let's write some code that can look for any arbitrary list of digits in pi:

```scheme
(define (find-in-pi ls)
  (let ([pi (make-pi-spigot)])
    (pi) ; skip the 3
    (let loop ([i 1] [l* '()])
      (let* ([d (pi)]
             [l* (map cdr (filter (lambda (ea)
                                    (and (not (null? ea))
                                         (= d (car ea))))
                                  (cons ls l*)))])
        (if (any? null? l*) (- i (length ls)) (loop (+ i 1) l*))))))
```

Using this, we can find the first time each digit occurs in pi:

```scheme
> (for/list ([i (in-range 10)]) (list i (find-in-pi (list i))))
'((0 31) (1 0) (2 5) (3 8) (4 1) (5 3) (6 6) (7 12) (8 10) (9 4))
```

Or the first time that longer sequences occur:

```scheme
> (find-in-pi '(1 2 3))
1923

> (find-in-pi '(4 5 6))
250

> (find-in-pi '(0 0 0))
600
```

Now, let's get crazy and see when [[wiki:867-5309/Jenny|Jenny's number]]() shows up:

```bash
┌ ☺ verkampj@minty ~/Projects/SmallProjects
└ time ./find-in-pi 8675309

8675309 is 9202591 digits into pi
```

I added a few more lines to the [full source](https://github.com/jpverkamp/small-projects/blob/master/blog/find-in-pi.rkt) that lets it run from the command line and compiled it with `raco exe find-in-pi.rkt`.

That took a while to run. :smile:
