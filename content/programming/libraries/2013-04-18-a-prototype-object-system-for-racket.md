---
title: A prototype object system for Racket
date: 2013-04-18 00:00:11
programming/languages:
- Racket
programming/topics:
- Object Oriented
---
As I seem to be [wont to do]({{< ref "2013-04-11-perlin-and-simplex-noise-in-racket.md" >}}), I needed something to work on my [Roguelike in Racket]({{< ref "2013-04-04-racket-roguelike-1-a-gui-screens-i-o-and-you.md" >}}) tutorial series--so I wrote it! This time, we're looking to add a {{< wikipedia page="Prototype-based programming" text="prototyped-based object system" >}} to Racket. I'm sure that someone has rigged up something similar before, but it's often more interesting to work things like this out for oneself.

<!--more-->

First, as a short aside, exactly what is a prototype-based object system? Well, Wikipedia says it clearly enough:

> **Prototype-based programming** is a style of {{< wikipedia "object-oriented programming" >}} in which {{< wikipedia page="Class (programming)" text="classes" >}} are not present, and behavior reuse (known as {{< wikipedia page="Inheritance (programming)" text="inheritance" >}} in class-based languages) is performed via a process of {{< wikipedia page="Cloning (programming)" text="cloning" >}}existing {{< wikipedia page="Object (programming)" text="objects" >}} that serve as {{< wikipedia page="Prototype" text="prototypes" >}}. This model can also be known as **classless**, **prototype-oriented** or**instance-based** programming. {{< wikipedia page="Delegation (programming)" text="Delegation" >}} is the language feature that supports prototype-based programming.

Essentially, rather than a dichotomy between classes and objects, everything is the same. If you want to instantiate a class, you clone it. If you want to extend a class, you clone it and add/override previous fields. So you should be able to do something like this:

```scheme
; Create a basic thing
(define-thing color [red 0] [green 0] [blue 0])

; Extend things
(define-thing red color [red 255])

; Get values, with optional default
(thing-get color 'red) => 0
(thing-get red 'red) => 255
```

Also, we want to be able to set values without altering the parent object:

```scheme
; Set value, existing or not
(thing-set! red 'red 1.0)
(thing-get red 'red) => 1.0
(thing-get color 'red) => 0
```

So how do we do this?

Well, to start with, we need something to store key/value pairs. It seems like {{< doc racket "Hash Tables" >}} will be the perfect option. So let's create a `thing` structure (it's not a perfect name, but I've seen worse).

```scheme
; A simple wrapper for things
(define-struct thing (data)
  #:constructor-name new-thing)
```

`#:constructor-name` is necessary since I want to define my own `make-thing`. Basically, we could directly return/use a `hasheq`. But this way, we get things like the `thing?` predicate and nice (if not particularly helpful) pretty printing:

```scheme
> (define-thing color [red 0] [green 0] [blue 0])
> color
#
```

So let's get down to it. What do we need to make a thing? Well, I want it to be semi-fancy (as you may have noticed already), so we're going to need to write a {{< doc racket "macro" >}}. Without it, we wouldn't be able to use values like `red`/`green`/`blue` without quoting them.

So here's a basic first version:

```scheme
; A very simple prototype based object system
(define-syntax make-thing
  (syntax-rules ()
    ; Add a key/value pair to a thing
    [(_ [k v] rest ...)
     (let ([thing (make-thing rest ...)])
       (hash-set! (thing-data thing) 'k v)
       thing)]
    ; Create an empty thing
    [(_)
     (new-thing (make-hasheq))]))
```

Basically, this will set up a chain of setting `key`/`value` pairs down until the base case which creates the hash itself. We could also create the objects directly in one line with something like this:

```scheme
(define-syntax-rule (make-thing [k* v*] ...)
  (new-thing
   (for/hash ([k (in-list '(k* ...))]
              [v (in-list (list v* ...))])
     (values k v))))
```

On the upside, that's much clearner, but on the downside it won't have the extra behavior that I'm going to add in just a moment (extending objects and inline procedure declarations).

So we have a basic system in place. Let's go ahead and write some quick setters/getters. These are actually really straight forward. At first, I wanted to have something where we could use un-quoted keys (which would require another macro), but that wouldn't allow us to pass variable values. So they're just functions. `thing-get` does allow for default values though, which should be helpful:

```scheme
; Access a value from a thing
(define (thing-get thing key [default (void)])
  (cond
    [(not (thing? thing))
     (error 'thing-get "~a is not a thing" thing)]
    [(or (not (void? default))
         (hash-has-key? (thing-data thing) key))
     (hash-ref (thing-data thing) key default)]
    [else
     (error 'thing-get "~a does not contain a value for ~a" thing 'key)]))

; Set a value in a thing
(define (thing-set! thing key val)
  (cond
    [(not (thing? thing))
     (error 'thing-set! "~a is not a thing" thing)]
    [else
     (hash-set! (thing-data thing) key val)]))
```

Nothing much to see here, it all works just like those tests that I defined above.

The next feature I wanted to add was object extension. This is particularly important for a prototype-based system, so we wanted to get it right. Essentially, you can pass an thing as the first argument to `make-thing` which will copy the values from that thing to the new one before assign key/value pairs. This also lets us override values in a clean manner:

```scheme
; A very simple prototype based object system
(define-syntax make-thing
  (syntax-rules ()
    ; Add a key/value pair to a thing
    [(_ [k v] rest ...)
     (let ([thing (make-thing rest ...)])
       (hash-set! (thing-data thing) 'k v)
       thing)]
    [(_ base [k v] rest ...)
     (let ([thing (make-thing base rest ...)])
       (hash-set! (thing-data thing) 'k v)
       thing)]
    ; Create an empty thing
    [(_)
     (new-thing (make-hasheq))]
    ; Copy an existing thing
    [(_ base)
     (if (thing? base)
         (new-thing (hash-copy (thing-data base)))
         (error 'make-thing "~a is not a thing to extend" base))]))
```

Having to duplicate the code between the first two cases is suboptimal, but I'm not sure how to fix it. Because matching will assign the first pair to `base` if it can, I kept getting infinite loops when I tried to combine the methods.

Now we can do things like this:

```scheme
> (define color (make-thing [red 0] [green 0] [blue 0]))
> (define red (make-thing color [red 255]))
> (thing-get red 'red)
255
> (thing-get color 'red)
0
```

That right there would be enough for what I have in mind. We have a full prototype-based system and methods to make getting/setting data easier. But there's one more trick I have up my sleeve. Like Racket's {{< doc racket "classes" >}}, I want to have a special syntax for calling methods. I want to be able to do this:

```scheme
> (define chatterbox (make-thing [(talk name) (format "~a says hello world!" name)]))
> (thing-call chatterbox 'talk "steve")
"steve says hello world!"
```

Instead of things like this:

```scheme
> (define chatterbox (make-thing [talk (lambda (name) (format "~a says hello world!" name))]))
> ((thing-get chatterbox 'talk) "steve")
"steve says hello world!"
```

Although optimally, the two methods can be used interchangeably, internally the former syntax should be converted into the latter. How do we do it? Well, add more to `make-thing`!

```scheme
; A very simple prototype based object system
(define-syntax make-thing
  (syntax-rules ()
    ; Create an empty thing, bind a function
    [(_ [(k arg* ...) body* ...] rest ...)
     (let ([thing (make-thing rest ...)])
       (hash-set! (thing-data thing) 'k
                  (lambda (arg* ...)
                    body* ...))
       thing)]
    [(_ base [(k arg* ...) body* ...] rest ...)
     (let ([thing (make-thing base rest ...)])
       (hash-set! (thing-data thing) 'k
                  (lambda (arg* ...)
                    body* ...))
       thing)]
    ; Add a key/value pair to a thing
    [(_ [k v] rest ...)
     (let ([thing (make-thing rest ...)])
       (hash-set! (thing-data thing) 'k v)
       thing)]
    [(_ base [k v] rest ...)
     (let ([thing (make-thing base rest ...)])
       (hash-set! (thing-data thing) 'k v)
       thing)]
    ; Create an empty thing
    [(_)
     (new-thing (make-hasheq))]
    ; Copy an existing thing
    [(_ base)
     (if (thing? base)
         (new-thing (hash-copy (thing-data base)))
         (error 'make-thing "~a is not a thing to extend" base))]))
```

Finally, we have everything we want. Now we have a short form for procedures in things as an analogue to the short form of {{< doc racket "define" >}}.

And `thing-call` is straightforward enough:

```scheme
; Call a function stored in a thing
(define (thing-call thing key . args)
  (cond
    [(not (thing? thing))
     (error 'thing-call "~a is not a thing" thing)]
    [(thing-get thing key #f)
     => (lambda (f)
          (if (procedure? f)
              (apply f args)
              (error 'thing-call "~a is not a procedure in ~a, it is ~a"
                     key thing f)))]
    [else
     (error 'thing-get "~a does not contain a value for ~a" thing 'key)]))
```

Have I mentioned before how much I like the `=>` form of `cond`?

One last note, what about `define-thing`? It's a direct merge of `define` and `make-thing`. 

```scheme
; Combine define and make-thing
(define-syntax-rule (define-thing name arg* ...)
  (define name (make-thing arg* ...)))
```

Scheme macros are particularly pleasant.

That's it. Now we have a fairly stable prototype system. Since it's backed by a `hasheq`, it should be relatively quick as well. 

If you'd like to download/use the code, you can do so here:
- <a href="https://github.com/jpverkamp/thing" title="thing on GitHub">thing source on GitHub</a>

It also makes use of the recently discovered (to me) `(module test+ ...)` behind the scenes. It lets you write testing cases that won't even be compiled unless you specifically need them. Read more about it here: {{< doc racket "Main and Test Submodules" >}}