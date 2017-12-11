---
title: Gregorian/Mayan conversion
date: 2013-01-25 14:00:30
programming/languages:
- Racket
- Scheme
programming/sources:
- Daily Programmer
slug: gregorian-and-mayan-dates
---
It may be 1 uinal, 15 kin too late for the new baktun, but I've got some neat code to convert back and forth between the {{< wikipedia "Gregorian calendar" >}} and the {{< wikipedia "Mayan calendar" >}}. It's based on a challenge on a post on the <a title="Daily Programmer Challenge #117 [Intermediate] Mayan Long Count" href="http://www.reddit.com/r/dailyprogrammer/comments/16obmx/011613_challenge_117_intermediate_mayan_long_count/">/r/dailyprogrammer subreddit</a>. As one might expect, the goal is to be able to take a year, month, and day in the Gregorian calendar and return the equivalent Mayan Long Count corresponding to that date. As a bonus (which of course I had to do :smile:), do the opposite and do it without using built in date functions.

<!--more-->

To start out, we want a structure for each (if you'd like, you can follow along <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/mayan-conversion.rkt" title="Mayan conversion on GitHub">here</a>):

```scheme
; date structures
(define-struct gregorian (year month day) #:transparent)
(define-struct mayan (baktun katun tun uinal kin) #:transparent)
```

Then, we'll need a few helpers. Particularly, we want a function that can calculate leap years and a list of days per month (ignoring any 29 day February for the time being).

```scheme
; test if a year is a leap year
(define (leap-year? year)
  (or (and (divisible? year 4)
           (not (divisible? year 100)))
      (divisible? year 400)))

; days per month
(define days/month '#(31 28 31 30 31 31 30 31 30 31 30 31))
```

Now we're ready to go. Eventually, we want to write the functions `gregorian->mayan` and `mayan->gregorian`, but it would be a bit of a pain to convert directly. So instead, we'll convert via the number of days since 1 January 1970. That will give us the functions `gregorian->days`, `days->gregorian`, `mayan->days`, and `days->mayan`. The `gregorian` functions are a bit more complicated, so we'll start with those.

First, `gregorian->days`. It's a bit sneaky, but it's a closed form solution. Basically, we need to know if we're before or after 0-day and if we're before or after February (for the leap years). After that, it's mostly a matter of mathy goodness.

```scheme
; convert from gregorian to days since 1 jan 1970
(define (gregorian->days date)
  ; a date after 1 jan 1970?
  (define go-> (>= (gregorian-year date) 1970))

  ; are we after February?
  (define feb+ (> (gregorian-month date) 2))

  ; range for leap years to test
  (define leap-range
    (list
     (if go-> 1970 (+ (gregorian-year date) (if feb+ 0 1)))
     (if go-> (+ (gregorian-year date) (if feb+ 1 0)) 1971)))

  (+ ; add year
     (* 365 (- (gregorian-year date) (if go-> 1970 1969)))
     ; add month
     (* (if go-> 1 -1) 
        (apply + ((if go-> take drop) days/month (- (gregorian-month date) 1))))
     ; add day
     (- (gregorian-day date) 1)
     ; deal with leap years
     (for/sum ([year (apply in-range leap-range)])
       (if (leap-year? year) (if go-> 1 -1) 0))))
```

The `for/sum` is the most potentially problematic point I think. I feel like there should be a non-looped solution to that, but this worked well enough (and it took long enough to get some of the other details working). In yet another tiny error that nevertheless took forever to track down, I originally had the second `(if feb+ ...)` the same as the first. Needless to say, that sent a few things sideways.

Next, we want to be able to invert that function. I couldn't work out a clean closed form for this one, so I just loop, first setting the year, then the month, then the day. It's a bit longer and I couldn't combine the forwards and backwards code, but it works well enough.

```scheme
; convert from days since 1 jan 1970 to gregorian date
(define (days->gregorian days)
  (cond
    ; work forward from 1 jan 1970
    [(> days 0)
     (let loop ([days days] [year 1970] [month 1] [day 1])
       (define d/y (if (leap-year? year) 366 365))
       (define d/m (if (and (leap-year? year) (= month 2))
                       29
                       (list-ref days/month (- month 1))))
       (cond
         [(>= days d/y)
          (loop (- days d/y) (+ year 1) month day)]
         [(>= days d/m)
          (loop (- days d/m) year (+ month 1) day)]
         [else
          (make-gregorian year month (+ day days))]))]
    ; work backwards from 1 jan 1970
    [(< days 0)
     (let loop ([days (- (abs days) 1)] [year 1969] [month 12] [day 31])
       (define d/y (if (leap-year? year) 366 365))
       (define d/m (if (and (leap-year? year) (= month 2))
                       29
                       (list-ref days/month (- month 1))))
       (cond
         [(>= days d/y)
          (loop (- days d/y) (- year 1) month day)]
         [(>= days d/m)
          (loop (- days d/m) year (- month 1) (list-ref days/month (- month 2)))]
         [else
          (make-gregorian year month (- d/m days))]))]
    ; that was easy
    [else
     (make-gregorian 1970 1 1)]))
```

Now that the two hard functions are out of the way, we get the easy ones. `mayan->days` is almost trivial, just a matter of multiplying each value by the correct multiple. Likewise, `days->mayan` works by repeated division (with remainder). I'd never before used the `define-values` / `quotient/remainder` pattern before, but it works really well.

```scheme
; convert from mayan to days since 1 jan 1970
(define (mayan->days date)
  (+ -1856305
     (mayan-kin date)
     (* 20 (mayan-uinal date))
     (* 20 18 (mayan-tun date))
     (* 20 18 20 (mayan-katun date))
     (* 20 18 20 20 (mayan-baktun date))))

; convert from days since 1 jan 1970 to a mayan date
(define (days->mayan days)
  (define-values (baktun baktun-days) (quotient/remainder (+ days 1856305) (* 20 18 20 20)))
  (define-values (katun katun-days) (quotient/remainder baktun-days (* 20 18 20)))
  (define-values (tun tun-days) (quotient/remainder katun-days (* 20 18)))
  (define-values (uinal kin) (quotient/remainder tun-days 20))
  (make-mayan baktun katun tun uinal kin))
```

After that, it's just a matter of wiring them together:

```scheme
; convert from gregorian to mayan
(define (gregorian->mayan date)
  (days->mayan (gregorian->days date)))

; convert from mayan to gregorian 
(define (mayan->gregorian date)
  (days->gregorian (mayan->days date)))
```

I love it when everything comes together like that. :smile:

Of course, we want to make sure to do some testing:

```scheme
; do some testing
(require rackunit)
(for ([test (in-list '((( 741  6 28)  -448705 ( 9 15 10  0  0))
                       ((1900  1  1)  -25567  (12 14  5  6 18))
                       ((1969  5 17)  -229    (12 17 15 13 16))
                       ((1970  1  1)   0      (12 17 16  7  5))
                       ((1970 10  1)   273    (12 17 17  2 18))
                       ((1987 10  1)   6482   (12 18 14  7  7))
                       ((1989  1 17)   6956   (12 18 15 13  1))
                       ((2012 12 21)   15695  (13  0  0  0  0))
                       ((2013  1 25)   15730  (13  0  0  1 15))))])

  (define g (apply make-gregorian (car test)))
  (define d (cadr test))
  (define m (apply make-mayan (caddr test)))

  (check-equal? (gregorian->days g) d)
  (check-equal? (days->gregorian d) g)
  (check-equal? (days->gregorian (gregorian->days g)) g)  

  (check-equal? (mayan->days m) d)
  (check-equal? (days->mayan d) m)
  (check-equal? (days->mayan (mayan->days m)) m)

  (check-equal? (gregorian->mayan g) m)
  (check-equal? (mayan->gregorian m) g))
```

Interestingly, it was 21 December 2012 that was the only case broken before I fixed the error in `days->gregorian`. So much for the end of the world...

This was actually a really neat program to work through. I'm glad that I stumbled across the <a title="Daily Programmer Challenge #117 [Intermediate] Mayan Long Count" href="http://www.reddit.com/r/dailyprogrammer/comments/16obmx/011613_challenge_117_intermediate_mayan_long_count/">Daily Programmer</a> challenges. With an easy problem each Monday, an intermediate one each Wednesday (like this one), and a hard one each Friday, there are more than enough interesting problems to keep me busy for quite a while.

As always, if you'd like to download the entire code, you can do so here:
<a href="https://github.com/jpverkamp/small-projects/blob/master/blog/mayan-conversion.rkt" title="Mayan conversion on GitHub">Mayan conversion source</a>
