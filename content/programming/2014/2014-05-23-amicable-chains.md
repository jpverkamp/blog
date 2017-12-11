---
title: Amicable chains
date: 2014-05-23 14:00:37
programming/languages:
- Racket
- Scheme
programming/topics:
- Graphs
- Mathematics
- Number Theory
---
Mathematicians are an odd bunch. Names for just about everyhing. There are {{< wikipedia page="Amicable number" text="amicable numbers" >}} and {{< wikipedia "perfect number" >}}, {{< wikipedia "sociable number" >}} and {{< wikipedia page="Betrothed number" text="betrothed numbers" >}}. There are {{< wikipedia "sublime number" >}}, {{< wikipedia "frugal number" >}}, and {{< wikipedia "quasiperfect number" >}}. Heck, there are {{< wikipedia "powerful number" >}}, {{< wikipedia "smooth number" >}}, and even {{< wikipedia page="Sphenic number" text="sphenic numbers" >}}. Rather a lot to deal with all told... So let's just focus on two of them: {{< wikipedia page="Perfect number" text="perfect numbers" >}} and {{< wikipedia page="Amicable number" text="amicable numbers" >}}.

<!--more-->

The two are rather related, in that they're both defined in terms of their sum of proper divisors. Start with divisors: the set of numbers that evenly divide a given number. So say the divisors of 25 are 1, 5, and 25. Proper adds the constraint that a number is not a divisor of itself (so only 1 and 5). Sum them and you have {{< inline-latex "spd(25) = 6" >}}. 

If {{< inline-latex "spd(n) = n" >}}, a number is considered perfect. If {{< inline-latex "spd(n) = m" >}} and {{< inline-latex "spd(m) = n" >}}, the {{< inline-latex "m" >}} and {{< inline-latex "n" >}} are amicable. Simple[^1] as that. The same context can be extended to a sequence:

{{< latex >}}\mathbb{X} = \left \{ x_n | spd(x_n) = x_{n+1}  \right \}{{< /latex >}}

So that's what we're dealing with today, given <a href="http://programmingpraxis.com/2014/05/20/amicable-chains/">Tuesday's post</a> on Programming Praxis. In a single sentence: find all perfect numbers, amicable pairs, and amicable chains less than one million.

Let's get started.

## Perfect numbers and amicable pairs

First we need to write a function that can quickly calculate the `sum-of-divisors` of a number. We'll be using the {{< doc racket "math/number-theory" >}} module to calculate divisors and <a href="http://pkg.racket-lang.org/#[memoize]">jbclements' `memoize` module</a> to save us a bit of time calculating a pile of these over and over again:

```scheme
(require math/number-theory
         memoize)

; Calculate sum of proper divisors (proper, thus subtracting i)
(define/memo (sum-of-divisors n)
  (- (apply + (divisors n)) n))
```

Testing it out with the value we already know:

```scheme
> (sum-of-divisors 25)
6
```

From here and with the definitions above, we can directly define perfect numbers:

```scheme
; A number is perfect if its divisors sum to itself
(define (perfect? n)
  (= n (sum-of-divisors n)))
```

And amicable pairs:

```scheme
; Two numbers are amicable if each numbers's sum of divisors is the other
(define (amicable? m n)
  (and (= m (sum-of-divisors n))
       (= n (sum-of-divisors m))))
```

As an example:

```scheme
> (perfect? 6)
#t
> (perfect? 25) ; (spd 25) -> 6
#f
> (amicable? 25 6)
#f
> (amicable? 220 284) ; (spd 220) -> 284; (spd 284) -> 220
#t
```

Looks good. But how about we think a little bit bigger, eh?

## Amicable chains

For the next part of the problem, we want to calculate *amicable chains*. Sequences of numbers of any length such that the sum of proper divisors of each number is the next and the chain wraps around at the end. On the smaller end, all perfect numbers are amicable chains of length 1. All amicable pairs are chains of length 2. One example amicable chain of length 5 would be `(12496 14264 14536 15472 14288)`[^2].

Given all of that, we should be able to write a nice recursive function to determine if a number is in an amicable chain and, if so, return it. To do so, we're going to essentially need to recur down a chain of numbers until one of three/four conditions is met:


* We find the original number in the sequence; return the amicable chain
* The chain terminates at 1 (any prime number will have 1 as the sum of divisors after which the chain will terminate)
* We find a number other than the original for the second time; there is a chain, but the number in question is not part of it (example 25 -> 6 which then loops)
* *optional:* The current number is larger than some bound; it may be a chain, but for our purposes return `#f`


Translating this relatively directly into code, we have:

```scheme
; An amicable chain is a sequence of numbers where each's sum of divisors is the next
; Ignore chains that leave the given bounds
(define (amicable-chain n [bound +inf.0])
  (let/ec return
    (let loop ([x (sum-of-divisors n)] [prev '()])
      (cond
        [(= x n)
         (cons x prev)]
        [(or (> x bound) (= x 1) (member x prev))
         (return #f)]
        [else
         (loop (sum-of-divisors x)
               (cons x prev))]))))
```

As given earlier:

```scheme
> (amicable-chain 12496)
'(12496 14264 14536 15472 14288)
> (amicable-chain 15472)
'(15472 14288 12496 14264 14536)
```

That gives us most of our framework. All that's left is extended it to a bunch of numbers at a time (and as a bonus: making a pretty picture).

## Generating a graph

Basic idea: Iterate through all numbers 2 through some bound. For each in turn, if it's an amicable chain, add the numbers in the chain to a graph. Skip any number added as we iterate upwards.

```scheme
; Create a graph of all amicable chains within the bounds
(define (amicable-chains-graph bound)
  (define graph (unweighted-graph/directed '()))
  (define colors (make-hash))

  (for ([i (in-range 2 bound)] #:unless (has-vertex? graph i))
    (cond 
      [(amicable-chain i bound) 
       => (λ (chain)
            (displayln chain)
            (for ([from (in-list chain)] 
                  [to (in-list (snoc (car chain) (cdr chain)))])
              (hash-set! colors from
                         (case (length chain)
                           [(1) 0] [(2) 1] [else 2]))
              (add-directed-edge! graph from to)))]))

  (values graph colors))
```

That's actually all there is to it. One interesting trick is iterating over the list `chain` and `(snoc (car chain) (cdr chain))`. Basically, that's a sneaky way to iterate over all sequential numbers in the list. `snoc` is the reversed form of `cons`. Rather than adding to the head of a list, add to the end. It's terribly inefficient, but at the very least it serves our purposes. 

With a helper wrapping the `graphviz` function to actually generate the files, and we can actually write out our results:

{{< figure src="/embeds/2014/amicable-chains.png" >}}

Looks like we have four perfect numbers (in red; 6, 28, 496, and 8128), a whole pile of amicable pairs, and two nice chains (the larger has almost 30 numbers). I'm actually a little surprised that such a large chain already appears under a million. It sort of makes me wonder just how large of chains there might be out there if you look further...

And that's it for today. As always, the code is on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/amicable-chains.rkt">amicable-chain.rkt</a>. Enjoy!

[^1]: For some definitions of simple
[^2]: Verification left as exercise to the reader