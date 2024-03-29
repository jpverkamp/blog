---
title: Narcissistic Numbers
date: 2012-12-14 11:00:16
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Mathematics
---
<a title="Programming Praxis: 115132219018763992565095597973971522401" href="http://programmingpraxis.com/2012/12/14/115132219018763992565095597973971522401/">Today's post</a> from Programming Praxis posits an interesting problem: how can we (efficiently) find all of the <a title="Wolfram Mathworld: Narcissistic numbers" href="http://mathworld.wolfram.com/NarcissisticNumber.html">narcissistic numbers</a> (in base 10)?

<!--more-->

First, we need to know just what a narcissistic number is. Relatively simply put, it's a number with *n* digits such that the sum of each digit raised to the *n*th power is the number itself. So 153 is a narcissistic number because *1<sup>3</sup> + 5<sup>3</sup> + 3<sup>3</sup> = 153*.

Furthermore, it turns out that we can establish an upper bound. Because the maximum such number would be all 9s, we only have a valid number if the following holds true:

{{< latex >}}n 9^n < 10^{n-1}{{< /latex >}}

This is true for {{< inline-latex "n \leq 60" >}}, so that will be our eventual upper bound (although the largest one is actually only 39 digits long: 115132219018763992565095597973971522401).

If you'd like to follow along, you can download the full source here:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/narcissistic.rkt" title="narcissistic source code on GitHub">narcissistic source code</a>

To start with, we know that simply directly enumerating all of the numbers is going to take a really long time, let along calculating all of those exponents. So let's try to do something a bit smarter. My idea is to recur on lists of digits. As we go, keep the list of digits and the sum of powers of those. Once the sum is too large, we can break that recursion since it will never have a solution.

So here's that initial code:

```scheme
; find all narcissistic numbers of length n
; narcissistic numbers are those which have the following property
; i = sum(d^n) for digit d in number i of length n
(define (narcissistic n)
  ; exponents
  (define expts (for/vector ([i (in-range 10)]) (expt i n)))

  ; upper bound on n
  (define bound (expt 10 n))

  ; find all numbers
  (sort
   (unique
    ; digits - digits added so far
    ; sum - the current sum of powers
    (let loop ([digits '()] [sum 0])
      (cond 
        ; if we have enough digits, check for a valid solution
        [(= n (length digits))
         (if (unordered-equal? digits (digits-of sum))
             (list sum)
             '())]

        ; if the sum is too large, bail out
        [(>= sum bound)
         '()]

        ; otherwise, recur on all possible digits
        [else
         (for*/list ([i (in-range 10)]
                     [res (in-list (loop (cons i digits) 
                                         (+ (vector-ref expts i) sum)))])
           res)])))
   <))
```

A few sample runs for *n = 3, 5, and 7*:

```scheme
> (time (narcissistic 3))
cpu time: 0 real time: 1 gc time: 0
'(153 370 371 407)

> (time (narcissistic 5))
cpu time: 15 real time: 8 gc time: 0
'(54748 92727 93084)

> (time (narcissistic 7))
cpu time: 62 real time: 58 gc time: 0
'(1741725 4210818 9800817 9926315)
```

That's all well and good, but we can do better. The next optimization I want to make is to avoid duplicating digit lists. Since I'm already comparing them where the order of digits doesn't matter, I can fix the recursive call (specifically in the *for*/list*) to only add digits at least as big as the ones we've already added. This requires another variable in the *loop*, but that's easy enough. Here's the modified version (with only the new *loop* code):

```scheme
; min - only add additional digits >= this
; digits - digits added so far
; sum - the current sum of powers
(let loop ([min 0] [digits '()] [sum 0])
  (cond 
    ; if we have enough digits, check for a valid solution
    [(= n (length digits))
     (if (equal? digits (sort (digits-of sum) >))
         (list sum)
         '())]

    ; if the sum is too large, bail out
    [(>= sum bound)
     '()]

    ; otherwise, recur on all possible digits (>= min)
    [else
     (for*/list ([i (in-range min 10)]
                 [res (in-list (loop i
                                     (cons i digits) 
                                     (+ (vector-ref expts i) sum)))])
       res)]))
```

(We also don't need either the *unordered-equal?* or *unique* any more since *digits* is guaranteed to be sorted in descending order, so that will help a bit.)

That's all of the optimizations I can think of at the moment, so with one additional method designed to run through all of the values from 1 to 60 (see the <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/narcissistic.rkt" title="narcissistic source code on GitHub">full source</a> for details), we're golden. Let's try it out:

```scheme
> (all-narcissistic)

1: 0 ms (0 ms total), 10 value(s)
(0 1 2 3 4 5 6 7 8 9)

3: 1 ms (1 ms total), 4 value(s)
(153 370 371 407)

4: 1 ms (2 ms total), 3 value(s)
(1634 8208 9474)

5: 5 ms (7 ms total), 3 value(s)
(54748 92727 93084)

6: 44 ms (51 ms total), 1 value(s)
(548834)

7: 36 ms (87 ms total), 4 value(s)
(1741725 4210818 9800817 9926315)

8: 86 ms (173 ms total), 3 value(s)
(24678050 24678051 88593477)

9: 186 ms (359 ms total), 4 value(s)
(146511208 472335975 534494836 912985153)

10: 376 ms (735 ms total), 1 value(s)
(4679307774)

11: 740 ms (1475 ms total), 8 value(s)
(32164049650 32164049651 40028394225
 42678290603 44708635679 49388550606
 82693916578 94204591914)

14: 4256 ms (9559 ms total), 1 value(s)
(28116440335967)

16: 12018 ms (28783 ms total), 2 value(s)
(4338281769391370 4338281769391371)

17: 19330 ms (48113 ms total), 3 value(s)
(21897142587612075 35641594208964132 35875699062250035)

19: 50583 ms (129151 ms total), 4 value(s)
(1517841543307505039
 3289582984443187032
 4498128791164624869
 4929273885928088826)

20: 90077 ms (219228 ms total), 1 value(s)
(63105425988599693916)

21: 147036 ms (366264 ms total), 2 value(s)
(128468643043731391252 449177399146038697307)

23: 355509 ms (951610 ms total), 5 value(s)
(21887696841122916288858 
 27879694893054074471405
 27907865009977052567814
 28361281321319229463398
 35452590104031691935943)

24: 543763 ms (1495373 ms total), 3 value(s)
(174088005938065293023722
 188451485447897896036875
 239313664430041569350093)

25: 803950 ms (2299323 ms total), 5 value(s)
(1550475334214501539088894
 1553242162893771850669378
 3706907995955475988644380
 3706907995955475988644381
 4422095118095899619457938)

27: 1662002 ms (5130340 ms total), 5 value(s)
(121204998563613372405438066 121270696006801314328439376 128851796696487777842012787 174650464499531377631639254 177265453171792792366489765)

29: 3223268 ms (10725563 ms total), 4 value(s)
(14607640612971980372614873089 19008174136254279995012734740 19008174136254279995012734741 23866716435523975980390369295)

31: 6078702 ms (21295307 ms total), 3 value(s)
(1145037275765491025924292050346 1927890457142960697580636236639 2309092682616190307509695338915)

32: 8255381 ms (29550688 ms total), 1 value(s)
(17333509997782249308725103962772)

33: 11122695 ms (40673383 ms total), 2 value(s)
(186709961001538790100634132976990 186709961001538790100634132976991)

34: 14724637 ms (55398020 ms total), 1 value(s)
(1122763285329372541592822900204593)

35: 19443557 ms (74841577 ms total), 2 value(s)
(12639369517103790328947807201478392 12679937780272278566303885594196922)

37: 33483043 ms (133828406 ms total), 1 value(s)
(1219167219625434121569735803609966019)

38: 42489389 ms (176317795 ms total), 1 value(s)
(12815792078366059955099770545296129367)

39: 54456508 ms (230774303 ms total), 2 value(s)
(115132219018763992565095597973971522400 115132219018763992565095597973971522401)

...
```

(That's as far as my run had made it when I went to bed. I'll let it run overnight and update with the final runtime for *n = 1 to 60* when it finishes.)

Not too bad. For comparison, here's the <a href="http://programmingpraxis.com/2012/12/14/115132219018763992565095597973971522401/2/" title="Programming Praxis: 115132219018763992565095597973971522401 solution">direct solution</a> from Programming Praxis running on the same machine (with some minor modifications to add timing):

```scheme
1 (0.17 ms)
2 (0.25 ms)
3 (0.53 ms)
4 (0.54 ms)
5 (0.70 ms)
6 (0.71 ms)
7 (0.72 ms)
8 (0.73 ms)
9 (0.73 ms)
153 (0.82 ms)
370 (0.94 ms)
371 (0.95 ms)
407 (0.98 ms)
1634 (1.72 ms)
8208 (6.64 ms)
9474 (7.78 ms)
54748 (75.36 ms)
92727 (108.07 ms)
93084 (108.47 ms)
548834 (580.60 ms)
1741725 (1914.96 ms)
4210818 (4851.30 ms)
9800817 (11564.71 ms)
9926315 (11715.81 ms)
24678050 (32655.09 ms)
24678051 (32655.34 ms)
...
```

Apparently Dik Winter generated the complete list in 1985 in about half an hour (from the Programming Praxis <a href="http://programmingpraxis.com/2012/12/14/115132219018763992565095597973971522401/2/" title="Programming Praxis: 115132219018763992565095597973971522401 solution">solution page</a> for this post), so I'm still a ways off (particularly with the improvements in processing power). But that's not too bad for a first/second try. Perhaps I'll see if I can't do better at some point in the future.

If you'd like to download the entire code for this project, you can do so on GitHub here:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/narcissistic.rkt" title="narcissistic source code on GitHub">narcissistic source code</a>