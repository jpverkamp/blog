---
title: Factoring factorials
date: 2014-01-27 14:00:22
programming/languages:
- Racket
- Scheme
programming/topics:
- Factorials
- Mathematics
- Number Theory
- Prime Numbers
---
There was <a href="http://programmingpraxis.com/2014/01/24/factoring-factorials/">a new post</a> on Programming Praxis a few days ago that seemed pretty neat:

> Given a positive integer n, compute the prime factorization, including multiplicities, of n! = 1 · 2 · … · n. You should be able to handle very large n, which means that you should not compute the factorial before computing the factors, as the intermediate result will be extremely large.

<!--more-->

The simple solution would be to directly use the {{< doc racket "math/number-theory" >}} module:

```scheme
(require math/number-theory)
(define (factor-factorial n)
  (factorize (factorial n)))
```

Quick to write and not terribly slow to run either:

```scheme
> (time (factor-factorial 10))
cpu time: 0 real time: 0 gc time: 0
'((2 8) (3 4) (5 2) (7 1))

> (time (factor-factorial 100))
...
cpu time: 359 real time: 356 gc time: 233

> (time (factor-factorial 250))
...
cpu time: 4071 real time: 4111 gc time: 2243
```

As hinted at in the problem statement though, we can do better. 

First of all, we don't have to recalculate factors. We're going to be calculating a lot of factors, each of which depends on others in turn. So let's take a hint from [[wiki:dynamic programming]]() and [[wiki:memoization]]() and keep a hash around of all the values we've factored thus far. Something like this:

```scheme
; Memoized version of prime factorization
(splicing-let ([cache (make-hash)])
  (hash-set! cache 1 (hash 1 1))
  (hash-set! cache 2 (hash 2 1))
  (define (prime-factors n)
    (hash-ref! 
     cache n
     (thunk
       (or
        (for/first ([i (in-range 2 (add1 (sqrt n)))] 
                    #:when (zero? (remainder n i)))
          (merge-hashes (prime-factors i) (prime-factors (/ n i))))
        (hash n 1))))))
```

There are a few neat pieces in that, which help a bit to make it more concise. First, {{< doc racket "splicing-let" >}} from {{< doc racket "racket/splicing" >}}. Basically, it's like a `let` in that the binding (the `cache`) is only visible within it's body, but unlike that, any `define` or similar form within it is at the outer scope. So we can call `prime-factors` even though we aren't in the let. Technically, this code would have done roughly the same thing:

```scheme
(define prime-factors
  (let ([cache (make-hash)])
    (λ (n)
      ...)))
```

But I've never particularly cared for that form. It's always seemed a bit ugly to me to split up the function name and actual definition (the λ) like that, even if it is a bit more clear how the scope goes. Either way works, however.

The next neat part is the use of {{< doc racket "hash-ref!" >}}. I wish I'd known about that years ago, but I can definitely use it now. Basically, it combines a `hash-ref` with a default value that is actually stored in the hash if it didn't previously exist. So it saves us the effort of checking first and updating if something is missing then returning. 

Finally, we have the {{< doc racket "for/first" >}} form. Basically, it's a `for` looping macro, but it will stop immediately the first time the body is executed. In this case, we'll run up from 2 to the square root, looking for any divisor. But since we're using `for/first`, it will short circuit with the first divisor and use the cache to avoid recalculating the same factors over and over again.

The final piece is `merge-hashes`. This isn't actually part of Racket, we'll have to write it ourselves:

```scheme
; Combine two hashes with numeric values by adding the values
(define (merge-hashes h1 h2)
  (define h (hash-copy h1))
  (for ([(k v) (in-hash h2)])
    (hash-update! h k (curry + v) 0))
  h)
```

Here's another neat hash function I wish I'd known about: {{< doc racket "hash-update!" >}}. Basically, you give it a key and update function. That update function is given the value at the key and gives back the new value to store. If the key doesn't exist, it uses the default. One note is that apparently the default value is passed to the update function as well. That certainly caused an interesting bug to track down... Oh, and the {{< doc racket "curry" >}}:

```scheme
(curry + v)
<=>
(λ (var) (+ var v))
```

It's a trick that I picked up when playing with <a href="http://www.haskell.org/haskellwiki/Haskell">Haskell</a>. It's pretty much necessary there (every function is curried), but it's kind of neat to use in Racket. It saves a few λs at the very least. 

Well, now we can factor things quickly. The next trick will be to speed up factoring factors. We don't want to actually calculate the factorial first, so instead we'll build up the factor list as we go:

```scheme
; Factor n! without actually calculating the factorial first
(define (factor-factorial n)
  (for/fold ([factors (hash)]) ([i (in-range 2 (+ n 1))])
    (merge-hashes factors (prime-factors i))))
```

{{< doc racket "for/fold" >}}, in this case, takes one or more accumulators (the hash) and one or more normal `for` terms. Each body will update the accumulators. Basically, it's the generic form that could be used to build all of the other for macros. Same as `fold` can be used to build rather a lot of other recursive functions. 

And there we have it. A quick printing function (code on <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/factoring-factorials.rkt">GitHub</a>) and we can compare to the naïve solution:

```scheme
> (time (print-factor-list (factor-factorial 10)))
2^8 + 3^4 + 5^2 + 7^1
cpu time: 0 real time: 3 gc time: 0

> (time (print-factor-list (factor-factorial 100)))
...
cpu time: 0 real time: 1 gc time: 0

> (time (print-factor-list (factor-factorial 250)))
...
cpu time: 0 real time: 2 gc time: 0
```

...

...

Yup.

That's faster. That's a lot faster.

```scheme
> (time (length (hash-keys (factor-factorial 10000))))
cpu time: 1123 real time: 1134 gc time: 1015
1229
```

So there are 1229 unique prime factors of 10,000! (which we can check with <a href="http://www.wolframalpha.com/input/?i=prime+factors+of+10000%21">Wolfram Alpha</a>, the number of factors is at the bottom). What's even better is that most of that time actually goes into the `length` and `hash-keys` functions. If you run just the `factor-factorial` function:

```scheme
> (time (begin (factor-factorial 10000) (void)))
cpu time: 187 real time: 181 gc time: 47
```

Shiny.

If you'd like to check out the entire code, you can do so on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/factoring-factorials.rkt">factor-factorial.rkt</a>