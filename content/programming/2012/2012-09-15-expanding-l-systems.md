---
title: Expanding L-systems
date: 2012-09-15 14:00:24
programming/languages:
- Scheme
slug: expandingl-systems
---
An [[wiki:L-systems|L-system]]() is essentially a set of rewriting rules that turns a simple set of rules into a complex pattern. They're generally used for generating self-similar fractals, including plant life, but I've also seen them used in programming languages research where they can generate valid programs given the grammar of a language. They're also rather similar to [turtle graphics]({{< ref "2012-04-13-wombat-ide-turtle-graphics.md" >}}) in that many of the sample graphics that I've [generated in the past]({{< ref "2012-04-13-wombat-ide-turtle-graphics.md" >}}) are based directly off the [[wiki:L-systems|L-systems page]]() on Wikipedia. So this time I've decided to work on a relatively simple macro that can be used to expand simple L-systems.

<!--more-->

The basic idea is that you want to take a set of rules and expand them. Let's start with with one designed to model algae growth from Lindenmayer himself (that's the L in L-system for anyone that didn't already know and hasn't clicked the links up above):

```
**variables** : A B
**constants** : none
**start**     : A
**rules**     : (A → AB), (B → A)
```

And a simple demonstration for how we might run that with the system I've developed:

```scheme
(define algae  ; an l-system is a one variable function (# of iterations)
  (l-system a  ; create a new l-system starting at a
    [a -> a b] ; bind a set of rules, each expanding a single non-terminal
    [b -> a]))

~ (algae 1)
 (a b)

~ (algae 2)
 (a b a)

~ (algae 3)
 (a b a a b)

~ (algae 4)
 (a b a a b a b a)
```

Or perhaps a slightly more complicated method that we can use to generate the same fern graphics that I've shown before with turtle graphics. This one also shows off the ability to generate nested structures inline. In the second rule, you can see several levels of nesting, all of which show up in the final result:

```scheme
(define fern
  (l-system x
    [f -> f f]
    [x -> f - [[x] + x] + f [+ f x] - x]))

~ (fern 2)
 (f f - ((f - ((x) + x) + f (+ f x) - x)) (+)
 (f - ((x) + x) + f (+ f x) - x) + f f (+) (f f)
 (f - ((x) + x) + f (+ f x) - x) - f - ((x) + x) + f (+ f x)
 - x)
```

Okay, enough demonstration, let's actually get to the heart of the code. Essentially, it's a single macro with two interlocking parts running inside. `deep-map` is a modified version of `map` that digs into nested lists while `expand` actually does the bulk of the work. I think my favorite part of the code is the call to `assoc` in the bottom. With that, the structure of the 2nd and later arguments to the macro really come in handy. It's times like these that Scheme's treatment of code as data and data as code really shine through.

```scheme
(define-syntax l-system
  (syntax-rules (->)
    [(l-system init rules ...)
     (lambda (n)

       (define (deep-map proc ls)
         (cond
           [(null? ls) '()]
           [(pair? (car ls))
            (cons (deep-map proc (car ls))
                  (deep-map proc (cdr ls)))]
           [else
            (cons (proc (car ls))
                  (deep-map proc (cdr ls)))]))

       (define (expand n ls)
         (if (zero? n)
             ls
             (apply append
               (deep-map
                 (lambda (x)
                   (let ([result (assoc x '(rules ...))])
                     (if result
                         (expand (sub1 n) (cddr result))
                         (list x))))
                 ls))))

       (expand n '(init)))]))
```

And that's all there is to it. There are a number of other features that I'd optimally like to add (conditional/branching outputs being one) but for a short bit of work, I don't think it's a half bad piece of code. 

If you'd like to download the full source code (with examples), you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/l-system.ss" title="l-system source">l-system source</a>