---
title: Trigonometric Triangle Trouble
date: 2014-05-02 14:00:26
programming/languages:
- Racket
- Scheme
programming/sources:
- Daily Programmer
programming/topics:
- Backtracking
- Geometry
- Mathematics
- Trigonometry
---
[Yesterday's post](http://www.reddit.com/r/dailyprogrammer/comments/24hr25/522014_challenge_160_hard_trigonometric_triangle/) at [/r/dailyprogrammer](http://www.reddit.com/r/dailyprogrammer/) managed to pique my interest[^1]:

> A triangle on a flat plane is described by its angles and side lengths, and you don't need all of the angles and side lengths to work out everything about the triangle. (This is the same as last time.) However, this time, the triangle will not necessarily have a right angle. This is where more trigonometry comes in. Break out your trig again, people.

<!--more-->

I am going to skip over a bit of the problem (that of parsing the input), but I think what's left is more than enough to make an interesting problem.

Thinking back to high school, triangles are defined by six pieces of information: three sides and three angles:

{{< figure src="/embeds/2014/triangle.png" >}}

But really, you only need any three pieces of those (with the exception of the three angles, with just that you have no sense of scale). More specifically, there are a set of relationships between the sides and angles in a triangle such that you can derive all six:

| Sum of angles | Rule of sines | Rule of cosines |
|---------------|---------------|-----------------|
| {{< latex >}}\alpha + \beta + \gamma = \pi{{< /latex >}} | {{< latex >}}\frac{a}{sin\ \alpha} = \frac{b}{sin\ \beta} = \frac{c}{sin\ \gamma}{{< /latex >}} | {{< latex >}} a^2 = b^2 + c^2 - 2bc\ cos\ \alpha {{< /latex >}} |

Sounds good, right? But how do we turn that into code?

First, we need some structure to work with. Perhaps a structure that represents the eventual information about the triangle that we are going to solve[^2]:

```scheme
; Represent a triangle as three angles and three sides
; Angles can be in either degrees or radians so long as all three are the same
; Any value is either numeric or #f if it is currently unknown
(struct triangle (∠ɑ ∠β ∠γ a b c) #:transparent)
```

Fair enough.

Next, how do we know when we're done? Since we're representing both angles and sides as numbers, we just need all six fields to be numeric. We could have a giant `and`, or we could play with a few neat functions. Specifically {{< doc racket "struct->" >}}:

```scheme
; If all six fields are numeric, we've solved the triangle
(define (solved? t)
  (andmap number? (cdr (vector->list (struct->vector t)))))
```

(If you'd like to follow along, the full code is here: [triangle-trouble.rkt](https://github.com/jpverkamp/small-projects/blob/master/blog/triangle-trouble.rkt))

We need that extra `cdr` in there since the first field is struct id (`triangle`).

Luckily though, that should be all of the framework we need for the moment. Next, we just need a solver.

At first glance, this might not look like a particularly recursive problem. In recursion, you need to be able to identify one or more base cases (in this case: the triangle is solved) and then break the problem into small steps, each of which is 'smaller' than the original problem. So if we can figure out how to at least make some progress / solve one additional side or angle, that should be good enough, right?

On first glance, the easiest solution would be to work out all of the possible cases. Perhaps we know a, b, and ∠ɑ. Perhaps ∠ɑ, ∠β, and c. But that's a lot of cases. Specifically:

{{< latex >}}{6 \choose 3} = 20{{< /latex >}}

We can do better than that.

Let's start with the framework:

```scheme
; Given some of the sides/angles of a triangle try to solve for the rest
(define (solve t)
  (let loop ([t t])
    (match t
      ; We have all three sides and angles, return
      [(? solved?) t]
      ; Two angles, solve for the third
      ...
      ; Sine rule
      ...
      ; Cosine rule
      ...
      ; Reorder
      ...)))
```

We're using {{< doc racket "match" >}} because `match` is awesome. More specifically because `match` is great at pattern matching against structs. For example, take the first case--two angles, solving for the third:

```scheme
...
; Two angles, solve for the third
[(triangle (? number? ∠ɑ) (? number? ∠β) #f a b c)
 (loop (triangle ∠ɑ ∠β (- pi ∠ɑ ∠β) a b c))]
...
```

Here we're matching against the six values that make up a triangle. For the first two clauses, we have the form `(? number? ∠ɑ)`. The `?` signifies that we are matching against a predicate, `number?`. The last part is the name we're binding to that value. After that, we're matching a literal `#f` (an unspecified third angle). Finally, we have the three sides. As they are, they will match any values, either numeric or `#f`.

So this case matches if and only if the first two angles are solved and the third is not, ignoring the sides for the moment. If this pattern doesn't match, we'll move on to the next (we'll deal with the case that it's ∠ɑ or ∠β that we're missing in a bit). Then, all we have to do is calculate the new value of ∠γ. Since Racket's trig functions work in radians[^3][^4], we'll subtract from 180° = π.

Straight forward. Now how about the sine rule. Well, it turns out that there are two cases we can use this for. Since we're relating matched sides and angles, we can take a matching side and angle along with *either* a second side or angle to solve for the other. More specifically, we can solve: ∠ɑ, a, ∠β → b or ∠ɑ, a, b → ∠β. In either case, we need to rearrange the equation slightly:

* ∠ɑ, a, ∠β → b
* {{< latex >}} = \frac{a}{sin\ \alpha} {{< /latex >}}
* {{< latex >}} b = \frac{a}{sin\ \alpha}\ sin\ \beta {{< /latex >}}

And another:

* ∠ɑ, a, ∠β → b
* {{< latex >}} \frac{sin\ \beta}{b} = \frac{sin\ \alpha}{a} {{< /latex >}}
* {{< latex >}}sin\ \beta = b \frac{sin\ \alpha}{a} {{< /latex >}}
* {{< latex >}} \beta = arcsin \bigl( b \frac{sin\ \alpha}{a} \bigr) {{< /latex >}}

Turning that into Racket and we have:

```scheme
...
; Sine rule 1: Matching side/angle + angle, solve for missing side
[(triangle (? number? ∠ɑ) (? number? ∠β) ∠γ
           (? number?  a)             #f   c)
 (loop (triangle ∠ɑ ∠β ∠γ a (/ (* a (sin ∠β)) (sin ∠ɑ)) c))]

; Sine rule 2: Matching side/angle + side, solve for missing angle
[(triangle (? number? ∠ɑ)            #f ∠γ
           (? number?  a) (? number?  b) c)
 (loop (triangle ∠ɑ (asin (/ (* b (sin ∠ɑ)) a)) ∠γ a b c))]
...
```

After that, we have the law of cosines. From here, we can work with two sides and the mismatched angle or directly with three sides:

* ∠ɑ, b, c → a
* {{< latex >}}  a^2 = b^2 + c^2 - 2bc\ cos\ \alpha {{< /latex >}}
* {{< latex >}}  a = \sqrt{b^2 + c^2 - 2bc\ cos\ \alpha} {{< /latex >}}

Second one:

* a, b, c → ∠ɑ
* {{< latex >}} b^2 + c^2 - 2bc\ cos\ \alpha = a^2 {{< /latex >}}
* {{< latex >}}  -2bc\ cos\ \alpha = a^2 - b^2 - c^2 {{< /latex >}}
* {{< latex >}}  cos\ \alpha = -\frac{a^2 - b^2 - c^2}{2bc} {{< /latex >}}
* {{< latex >}}  \alpha = arccos\bigl(-\frac{a^2 - b^2 - c^2}{2bc}\bigr) {{< /latex >}}

In Racket:

```scheme
...
; Cosine rule 1: Angle and the other two sides, solve for third side
[(triangle (? number? ∠ɑ)           ∠β             ∠γ
           #f             (? number?  b) (? number?  c))
 (loop (triangle ∠ɑ ∠β ∠γ (sqrt (+ (sqr b) (sqr c) (- (* b c (cos ∠ɑ)))))))]

; Cosine rule 2: Three sides, solve for one angle
[(triangle #f                        ∠β             ∠γ
           (? number?  a) (? number?  b) (? number?  c))
 (loop (triangle (acos (/ (+ (sqr b) (sqr c) (- (sqr a))) (* 2 b c))) ∠β ∠γ a b c))]
...
```

Those are all of the hard cases. But as I said, we still have to deal with reordering. Here's where one concession that I'm making compared to the original problem comes into play: I do not care what order the final sides / angles are in, just so long as the triangles are equivalent. So we're perfectly fine to rotate the sides and angles, just so long as we do it to both:

```scheme
...
; Try another ordering
[(triangle ∠ɑ ∠β ∠γ a b c)
 (loop (triangle ∠β ∠γ ∠ɑ b c a))]
```

This won't *quite* work though. Can you see why?

Well what happens if the variables are just ordered badly. Right now, it's possible that none of the cases will trigger in any of these three orderings. What happens then?

Well, right now we'll keep looping forever.

Oops.

There are a few ways that we can deal with this. We could keep a counter. If we've tried three rotations without moving forward, we're done. But even more elegant (in my mind), we could keep a list of partial solutions we've already tried. Even better, that will let us backtrack. So if we get to a case we've already seen (that didn't work), back up naturally using the structure of recursion. All together, it will look something like this:

```scheme
; Given some of the sides/angles of a triangle try to solve for the rest
(define (solve t)
  (define tried '())
  (let loop ([t t])
    (set! tried (cons t tried))
    (match t
      ; We have all three sides and angles, return
      [(? solved?) t]
      ; We've already tried this solution, backtrack
      [(? (curryr member (cdr tried)))
       #f]

      ...)))
```

We could have done without the explicit mutation, either using a {{< doc racket "parameter" >}} to make the dynamic scope more obvious or by passing the `tried` variable around in the loop. Personally though, I think this is probably the 'cleanest' solution.

So plug in the rules from above and we're good to go, right?

Well, not quite. There are still a few ordering issues. Sometimes the sides and angles just aren't lined up 5 rules that we have. So the last thing we need is a second ordering rule:

```scheme
...
; Try another ordering
[(triangle ∠ɑ ∠β ∠γ a b c)
 (or (loop (triangle ∠β ∠γ ∠ɑ b c a))
     (loop (triangle ∠β ∠ɑ ∠γ b a c)))]
```

This is actually pretty elegant for two reasons: Because we return `#f` when we backtrack, that will go to the second case if and only if the first doesn't find a solution. This works because anything not exactly `#f` in Racket is true and `or` returns the first non-`#f` argument (if one exists).

And that's it. It can already solve a good number of problems:

```scheme
> (solve (triangle #f #f #f 1 1 (sqrt 2)))
(triangle 0.785 0.785 1.571 1 1 1.414)

> (solve (triangle (/ pi 2) #f #f (sqrt 2) 1 #f))
(triangle 0.785 0.785 1.571 1 1.000 1.414)

> (solve (triangle (/ pi 3) (/ pi 3) #f #f #f 3))
(triangle 1.0472 1.0472 1.0472 2.999 2.999 3)
```

We do have a fair few rounding errors creeping in, but unfortunately that's just part of the price we have to pay when working with real (analog) numbers in a digital computer.

And that's pretty much it. Or it would be, if not for one little extra feature I wanted to throw in. Remember how I said that because Racket's trig functions deal in radians, so too would our triangles? Well, just in case, here are a few conversion functions (since {{< doc racket "radians->degrees" >}} and {{< doc racket "degrees->radians" >}} are both built in if you're using the full {{< doc racket "racket" >}} module):

```scheme
; Convert all angles in a triangle from radians to degrees
(define (triangle-radians->degrees t)
  (define (r->d ∠) (and ∠ (radians->degrees ∠)))
  (match t
    [(triangle ∠ɑ ∠β ∠γ a b c)
     (triangle (r->d ∠ɑ) (r->d ∠β) (r->d ∠γ) a b c)]
    [#f #f]))

; Convert all angles in a triangle from degrees to radians
(define (triangle-degrees->radians t)
  (define (d->r ∠) (and ∠ (degrees->radians ∠)))
  (match t
    [(triangle ∠ɑ ∠β ∠γ a b c)
     (triangle (d->r ∠ɑ) (d->r ∠β) (d->r ∠γ) a b c)]
    [#f #f]))

; Given some of the sides/angles of a triangle try to solve for the rest
(define (solve/radians t)
  (define tried '())
  (let loop ([t t])
    ...))

; Given some of the sides/angles of a triangle try to solve for the rest
(define (solve/degrees t)
  (triangle-radians->degrees (solve/radians (triangle-degrees->radians t))))
```

Now you can solve the examples given in the problem:

```scheme
> (solve/degrees (triangle 39.0 56.0 #f 2.45912 #f #f))
(triangle 56.0 85.0 39.0 3.240 3.893 2.459)

> (solve/degrees (triangle 43.0 #f 70.0 #f #f 7))
(triangle 43.0 67.0 70.0 5.080 6.857 7)
```

And that's it. You can find the full code on GitHub here: [triangle-trouble.rkt](https://github.com/jpverkamp/small-projects/blob/master/blog/triangle-trouble.rkt)

Bonus round:
1) Without actually running it, can you figure out what will happen if you give it an impossible triangle? Such as three angles or two angles already too large?

Bonus bonus round:
2) What about cases with three sides that *should* be impossible but technically have a solution[^5]... Such as a=1, b=2, c=4.

[^1]: Or is it peek? Peak?
[^2]: I love Racket's / DrRacket's native unicode support, having the ∠ character in a variable name is just cool
[^3]: As do most sane languages
[^4]: Although I'm sure there are those that don't...
[^5]: If only you can imagine
