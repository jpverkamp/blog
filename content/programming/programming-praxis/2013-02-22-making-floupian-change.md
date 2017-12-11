---
title: Making Floupian Change
date: 2013-02-22 14:00:45
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
---
On the island of Floup in the South Pacific ((not a real place)), one might find coins worth 1, 3, 7, 31, or 153 floupia each. In addition, they have a most curious custom. Whenever one makes a payment of any sort, it is considered rude not to minimize the total number of coins involved in the exchange. For example, if someone were to purchase a nice refreshing beverage for 17 floupia ((the floupia is currently performing rather well against the dollar)), one might pay with three 7f coins and receive a 1f and a 3f coin in exchange for a total of 5 coins. But that would be terrible, as a more efficient solutions exists: pay a single 31f coin and receive two 7f coins as change.

<!--more-->

Today's challenge on <a title="Floupia" href="http://programmingpraxis.com/2013/02/22/floupia/">Programming Praxis</a> (a guest submission!) is to write a program that can make change in any situation, should you be visiting Floup or a Floupian traveling abroad. No matter the coinage, it should be possible to minimize the transaction.

To start, my goal is to make use of the functional programming model and write one function to set up a coin system which will in turn return the function that makes change. One could do much the same thing with an object oriented model. So the final structure we're looking at will be something like this:

```scheme
; define a function that will accept payment from a list of coins
(define (make-coinage coins)
  ...

  ; make a payment of a given value
  (define (make-payment value)
    ...)

  ; return the payment function
  make-payment)
```

Optimally, this will allow us to run this:

```scheme
> (define floupia (make-coinage '(1 3 7 31 153)))
> (floupia 17)
'((31) (7 7))
```

So what do we need to write the internal `make-payment` function? 

Well, my first thought was to start with the value we're trying to pay. Then, recursively try paying with each coin in turn until we've paid the entire bill. Unfortunately, in this original plan, I neglected to take into account the fact that we need to minimize both the number of coins in the payment and in the change. That's okay though, the code was already getting ugly. :smile:

So for the second try, we're going to think about the problem the other way. Start by generating all possible combinations of *n* coins (starting with *(= n 1)*). For each combination, calculate each possible way to split the coins between the payment and change. For each split, check if the difference between the two is the target value. If so, the first solution we find is the minimal one (since we start with 1 coin and count up). It's terribly inefficient, but it's guaranteed to find a solution if one exists.

For that to work though, we need to be able to generate coin lists. So we need a helper function:

```scheme
; generate all lists of n coins
(define (make-coin-list n-coins)
  (cond
    [(= n-coins 0) '(())]
    [else
     (for*/list ([coin (in-list coins)]
                 [sublist (in-list (make-coin-list (- n-coins 1)))])
       (cons coin sublist))]))
```

Simple enough. `for*/list` makes a set of nested loops that say for each possible new coin, add it to each (recursive) list of one less coin. Add in the base case of zero coins and we're good to go. ((Challenge: Returning `'()` in the base case doesn't work at all. Can you figure out what it would do and why (without running it)? ))

Now that we have that, we're ready to do the bulk of the problem:

```scheme
; make a payment of a given value
(define (make-payment value)
  (call/cc 
   (lambda (return)
     ; avoid staring contests
     (unless (zero? (remainder value (apply gcd coins)))
       (return #f))

     ; loop up through possible numbers of coins
     ; and each split within that of payment and change
     (for ([n-coins (in-naturals)])
       (for* ([coin-list (in-list (make-coin-list n-coins))]
              [split-at (in-range (+ 1 (length coin-list)))])
         ; if we have a valid payment, this is a minimal solution
         (define payment (take coin-list split-at))
         (define change (drop coin-list split-at))
         (when (= (- (apply + payment) value) (apply + change))
           (return (list payment change))))))))
```

It's a bit of a blog of code, but I think it all builds pretty naturally. The `call/cc` sets up a break points so we can return immediately when we find a solution. The outer loop counts upwards for the number of coins. The inner nested `for*` will try each coin list and for each list all possible splits. Then we pull apart the list and check if it's a valid solution. ((Challenge: Identify all of the relatively inefficient function calls in this code. There are at least half a dozen. :smile:))

Let's give it a few tries:

```scheme
> (define floupia (make-coinage '(1 3 7 31 153)))
> (floupia 17)
'((31) (7 7))
> (floupia 99)
'((1 7 153) (31 31))
> (floupia 57)
'((1 1 31 31) (7))
```

It also works perfectly well for non-floupian currency:

```scheme
> (define us (make-coinage '(1 5 10 25 50 100)))
> (define uk (make-coinage '(1 2 5 10 20 50 100 200)))
> (us 119)
'((10 10 100) (1))
> (us 123)
'((25 100) (1 1))
> (uk 119)
'((20 100) (1))
> (uk 123)
'((1 2 20 100) ())
```

Heck, if you wanted, you could even use {{< wikipedia page="Money in harry potter#Economy" text="Knuts, Sickles, and Galleons" >}}!

```scheme
> (define harry-potter (make-coinage '(1 17 493)))
> (harry-potter 100)
'((17 17 17 17 17 17) (1 1))
```

So now you know, if you're every buying a 1000 Knut keepsake from a Floupian wizard, you should pay with 6 Sickles and expect 2 Knuts in return. :smile:

That's all there is. This was a really fun problem to work through. It's interesting when a problem makes you think through a relatively common situation (making change) in an uncommon way. 

If you'd like to see/download the entire source in one place, it's available on GitHub:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/floupia.rkt" title="Floupia source on GitHub">Floupia source</a>

**Edit:** It turns out that there were two small(ish) problems with the code as posted.

First, as pointed out in the comments, there are some coin systems which would result in non-stable transactions. For example, if you had only 3c and 6c coins, how could you pay for an 11c item? It may be rude to involve more coins than absolutely necessary, but just imagine how rude it would be to stand there staring at one another... forever. 

All you need to do is check the `gcd` though. If the `value` you're trying to make change for is not divisible by the `gcd` of the `coins`, then there's no valid solution. So just add this right inside of the `call/cc` (added above):

```scheme
; avoid staring contests
(unless (zero? (remainder value (apply gcd coins)))
  (return #f))
```

Now, if there's no solution you'll get `#f` back:

```scheme
> (define strangeness (make-coinage '(3 6)))
> (strangeness 12)
'((6 6) ())
> (strangeness 11)
#f
```

Second, we weren't actually checking all of the splits. I'd forgotten one of the most basic rules: check your edge cases. It turned out that with the original code, the case where one could pay with exact change and get nothing in return was being ignored. So I've added a `(+ 1 ...)` to the range check that will fix that. It slightly alters a few of the answers actually (and in one case finds a better one). There's something to be said for always calculating test cases by hand.
