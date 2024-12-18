---
title: 'Adventures in optimization, re: Typed Racket'
date: 2013-04-16 14:00:47
programming/languages:
- Racket
- Scheme
programming/topics:
- Graphics
- Mathematics
- Noise
- Optimization
- Type Systems
---
Last Thursday I wrote a [post about generating Perlin/simplex noise]({{< ref "2013-04-11-perlin-and-simplex-noise-in-racket.md" >}}) in Racket. Later that day, I <a title="[racket] Perlin and simplex noise - optimizing Racket code" href="http://lists.racket-lang.org/users/archive/2013-April/057245.html">posted to the Racket mailing list</a> asking how I could make it faster. What resulted was a whole sequence of responses (primarily about Typed Racket) and a bit of a rabbit hole that I'm still trying to wrap my head around.

<!--more-->

The first version that I tried to run was the original untyped code which used the {{< doc racket "picturing-programs" >}} teachpack to generate an image. Running Racket 5.3.3 on an x86_64 Linux machine, here are the timing results (if you'd like to try it yourself, use <a href="https://github.com/jpverkamp/noise/tree/b2d12e4">git b2d12e4</a>):

```
 perlin: cpu time: 355 real time: 356 gc time: 40
simplex: cpu time: 243 real time: 242 gc time: 4
```

That's actually much better than I originally got on my 64-bit Windows 7 machine, despite a slightly faster CPU from the same year. I'm still not sure sure why that's the case.

But that's not what I'm interested in at the moment. :smile: What's more interesting right now is when I started trying to optimize things.

Based on the first few emails, the way to go seemed to convert my code to Typed Racket. So the first thing that I did was to swap out the `#lang` line from `#lang racket` to `#lang typed/racket`. Of course when I did that, all hell broke loose with page upon page of errors of the sort:
<pre style="color: red;">Type Checker: Expected Real, but got Any in: x
Type Checker: Expected Vector, but got Any in: g
Type Checker: Expected Number, but got Any in: x
Type Checker: Expected Vector, but got Any in: g
...</pre>
Yeah... Basically Racket is telling me that it knows I'm trying, but I'm going to have to give it a few more (read: any) types before it can help me.

So I go through and I start typing[^1] things. One caveat is that there are at least two ways to assign a type to things in Typed Racket. Either you can declare the types inline, using forms like `define:` and `let:` or you can keep the code as it was and add the type signatures with just `:`.

As an example, the definition of `grad3` could be:

```scheme
; using inline types
(define: (grad3 : (Vectorof (Vectorof Integer)))
  '#(#( 1  1  0) #(-1  1  0) #( 1 -1  0) #(-1 -1  0)
     #( 1  0  1) #(-1  0  1) #( 1  0 -1) #(-1  0 -1) 
     #( 0  1  1) #( 0 -1  1) #( 0  1 -1) #( 0 -1 -1)))

; using type annotations
(: grad3 (Vectorof (Vectorof Integer)))
(define grad3
  '#(#( 1  1  0) #(-1  1  0) #( 1 -1  0) #(-1 -1  0)
     #( 1  0  1) #(-1  0  1) #( 1  0 -1) #(-1  0 -1) 
     #( 0  1  1) #( 0 -1  1) #( 0  1 -1) #( 0 -1 -1)))
```

Since the only other experience I had with something like this was in Haskell, the latter seemed more natural to me. I later <a href="http://lists.racket-lang.org/users/archive/2013-April/057256.html">asked</a> on the mailing list and <a href="http://lists.racket-lang.org/users/archive/2013-April/057263.html">the answer</a> was basically that either is perfectly valid. 

Going through the rest of the code and adding types was rather straight forward. I knew from previous (minimal) optimization experience in Racket that using `Flonum` was probably what I wanted to do, so everything essentially became either `Integer` or `Flonum`. The most interesting / relevant type is probably that of the `perlin` function itself (`simplex` has the same type):

```scheme
(: perlin
   (case-> (Flonum -> Flonum)
           (Flonum Flonum -> Flonum)
           (Flonum Flonum Flonum -> Flonum)))
```

This is a bit ugly, but essentially what it's saying is that `perlin` can have multiple types for each of the optional arguments, but it always takes in `Flonum`s and returns a `Flonum`. It doesn't seem like there's a way to directly specify optional parameters in Typed Racket (yet), but for the time being, `case->` gets the job done well enough. 

In addition, we had to add in a bunch of types within the `perlin`/`simplex` functions. I probably added more than I needed to, typing every variable that I had, but I figured that if I had to type any of them I might as well go all of the way. So throughout the function, I have lines like these:

```scheme
(: gi000 Integer) (: gi001 Integer) (: gi010 Integer) (: gi011 Integer)
(: gi100 Integer) (: gi101 Integer) (: gi110 Integer) (: gi111 Integer)

...

(: n000 Flonum) (: n001 Flonum) (: n010 Flonum) (: n011 Flonum)
(: n100 Flonum) (: n101 Flonum) (: n110 Flonum) (: n111 Flonum)
```

Not particularly pretty, but not too painful either.

What did get annoying however was after I had everything typed and I still got this particularly pleasant error:
<pre style="color: red;">Type Checker: No function domains matched in function application:
Domains: Flonum Flonum Flonum
         Flonum Flonum
         Flonum
Arguments: Zero</pre>
It turns out that Racket knows that zero times anything is zero. The problem is that zero times anything is exactly 0, the real, exact, integer version of the number (Actually it has it's own type: `Zero`). But that's not what we're looking for, we're looking for a `Flonum`. I could work around it using either the function `exact->inexact` or the function `real->double-flonum`, but both of those had to be applied in the code using `perlin`, leaking the implementation details in a rather unsatisfactory way (since I can imagine that many if not all uses of noise would eventually use the point 0, 0).

Still, it was enough for a first try. I don't have timing results for this on the same machine as the rest, but if you'd like to try it out, you can get the code using <a href="https://github.com/jpverkamp/noise/tree/f33f6d7">git f33f6d7</a>.

About this time, I got <a href="http://lists.racket-lang.org/users/archive/2013-April/057255.html">another email</a> back that detailed essentially what I'd been trying to do, only they had a few tricks that I hadn't been able to find by myself. Specifically:

* [images/flomap](http://pre.racket-lang.org/docs/html/images/flomap_title.html) has a faster (typed) image generator ({{< doc racket "build-flomap*" >}}) than {{< doc racket "picturing-programs" >}} 
* `case->` slows down typechecking (but has no effect on runtime)
* [exact-floor](http://docs.racket-lang.org/reference/generic-numbers.html#\(def._\(\(lib._racket/math..rkt\)._exact-floor\)\)) is far faster than using {{< doc racket "inexact->exact" >}} and {{< doc racket "floor" >}}
* shadowing (rather than `set!`) should allow for better optimization, especially with floating point numbers
* `Real` can be used as the type for `Real` numbers, including the `Zero` that was causing so much trouble

Using all of that, I set about a second round of optimizations. Primarily, since Real allowed for `Zero`, I converted every `Flonum` to `Real`, along with the rest of the previously specified changes. Here are the timing results using the typed code using Real for the numerics and generating an image using the <a href="http://pre.racket-lang.org/docs/html/images/flomap_title.html" data-pltdoc="x">images/flomap</a> library. Between the two of them, we got a substantial boost for both Perlin and simplex noise (<a href="https://github.com/jpverkamp/noise/tree/006faf9">git 006faf9</a>):

```
 perlin: cpu time: 235 real time: 236 gc time: 15
simplex: cpu time: 147 real time: 147 gc time: 4
```

Overall, it's about 2x faster than the original code, and all for just adding the type annotations.

The next step suggested to me was to use Racket's {{< doc racket "Optimization Coach" >}}. Essentially, it's a tool built into DrRacket for use with Typed Racket that will color code your code based on how successful the compiler will be on optimizing your functions. Specifically, it will be green if it can manage to inline your code and avoid boxing/unboxing values and also apply floating point specific functions (where necessary).

The problem was, running through the code I had, there was a heck of a lot of red... Running through my code, there was a heck of a lot of red:

{{< figure src="/embeds/2013/optimization-errors.png" >}}

Drilling down into the errors (it took a while to realize that right clicking would give more detail), it eventually turned out that converting from `Flonum` to `Real` was actually *causing* more errors than it was solving. Since `Real` is more generic and includes `Integer`s as well as `Flonum`s, it wasn't possible for the compiler to use pure floating point functions although we both knew it wanted to. So back to `Flonum` we went![^2]

Actually, no. I'm not really sure why, but at this point, I decided that I liked `Float` better than `Flonum`. It turns out that the two are essentially aliases for one another (which doesn't help when it's not consistent which will appear in error messages), so I could have used either. In the end, I switched to `Float` though. I think it was mostly because of experience with other languages. `Float` is a common term, `Flonum` is less so.

In any case, my next pass was to turn `Real` *back into* `Float`. So it goes. This time though, I made one tweak that would allow the best of both worlds:

```scheme
(: perlin (case-> (Real -> Float)
                  (Real Real -> Float)
                  (Real Real Real -> Float)))
(define (perlin x [y 0.0] [z 0.0])
  (perlin^ (real->double-flonum x)
           (real->double-flonum y)
           (real->double-flonum z)))

(: perlin^ (Float Float Float -> Float))
(define (perlin^ x y z)
  ...)
```

Since I was would only `provide` `perlin`, not `perlin^`[^3], I could have a function that accepted any real number but internally use `Floats` for all of my types.

I ran the Optimization Coach again and the results were beautiful:

{{< figure src="/embeds/2013/optimization-better.png" >}}

Green, beautiful green. I knew there was a reason it was my favorite color. Better yet, all that green is telling me that the compiler should (theoretically) be able to eek out even more speed, yes? Well, here are the timing results for using `Float` instead of `Real` and writing the aforementioned wrapper to convert between the two.

```
 perlin: cpu time: 112 real time: 118 gc time: 23
simplex: cpu time: 106 real time: 110 gc time: 3
```

Yes! More speed! We're down to about 1/10th of a second for 65,536 calls to either function. That's none too shabby.

But finally, I wanted to test how much of that was overhead in generating the image and how much was actually the noise algorithms. So I just wrote a simple nested `for` loop to generate the 256x256 calls to Perlin/simplex. At first it was slower. It turns out that even that had to be typed otherwise the untyped Racket code would eat up any meager benefits I'd gained. So I added types to my simple test bench as well. Here are the results (<a href="https://github.com/jpverkamp/noise/tree/7445311">git 7445311</a>):

```
 perlin: cpu time: 41 real time: 40 gc time: 0
simplex: cpu time: 52 real time: 52 gc time: 2
```

That's none too shabby at all. Actually, if you compare it to the <a title="PDF describing Perlin and simplex noise" href="http://webstaff.itn.liu.se/~stegu/simplexnoise/simplexnoise.pdf">original algorithm</a> my code is based on (written in Java, not C as I originally stated) it's well within the same order of magnitude. In the Java code, without generating an image, generating a 256x256 simplex grid takes an average of 30 ms.

All things considered, I'm pretty happy with my results. It is mildly puzzling that up until the very final test case the results for Perlin are always slower than simplex (which is to be expected given the relative runtimes of the algorithms[^4]) , but in the last case they're exactly the same. If anyone has a good reason for why that might be, I'd love to hear it.

Well, that's all I have. Working with Typed Racket was actually a surprisingly pleasant experience. It reminded me of all of the better parts of <a title="Haskell" href="http://www.haskell.org/haskellwiki/Haskell">Haskell</a>, where you can add type annotations to make the compiler work with you rather than against you.

[^1]: Whee typing vs typing
[^2]: This is all actually mentioned in the Racket {{< doc racket "documentation on optimization" >}}.
[^3]: Sorry Suzanne, but the hats must live on
[^4]: *O(n!)* for Perlin and *O(n<sup>2</sup>)* for simplex, where *n* is the number of dimensions if I understand correctly