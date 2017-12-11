---
title: Bitvectors in Racket
date: 2012-10-29 14:00:50
programming/languages:
- Racket
- Scheme
programming/topics:
- Data Structures
---
A bit shorter on time today, so I've just got a quick library that I worked out to solve another problem (I'll post it later this week when it's actually working). Basically, when you need to store a heck of a lot of binary flags and don't want to waste space, the best way to do it would be as one long list of bits. It's really easy to do in a language like C, but how can you do it in Racket?

<!--more-->

Well, it turns out it's not that much more difficult. You just have to know where to look. Let's start with creating the bytevector. Basically, we need one byte for every eight bits we want to store in the vector. Easy enough:

```scheme
; create a bitvector
(define (make-bitvector size [default #f])
  (make-bytes (ceiling (/ size 8)) (if default #xff #x00)))
```

Easy enough, although printing them out isn't too pretty at the moment:

```scheme
> (make-bitvector 20)
#"\0\0\0"

> (make-bitvector 20 #t)
#"\377\377\377"
```

We'll work on that in a bit. First, how can we pull out a bit from a bitvector? To do that, you need to know a few functions (`bitwise-and` and `arithmetic-shift` to start with). As an example, consider the case where you have the bit pattern `0001000101` and want to pull out the bit at index `4`.

First, get the correct byte:

```
/      \ /      \
00010001 01------
   /\
   ||
```

Next, get the correct bit. This is where the `arithmetic-shift` comes in. Essentially, it's a much faster way of calculating powers of two. So `(arithmetic-shift 1 4) = 16 = 00001000`.

```
/      \
00010001 <- bitvector
00001000 <- mask
00000000 <- result (0 is #f, anything else is #t)
```

After that, we actually have what we'd need to display bitvectors. I just wrote a simple method that will loop over a bitvector and turn it to a string of 1s and 0s. Since we aren't storing the size with the bitvector, you need to specify it here.

```scheme
; used to print out a bitvector
; the size is necessary to avoid printing the extra bits
(define (bitvector->string bv size)
  (list->string
   (for/list ([i (in-range size)])
     (if (bitvector-ref bv i) #\1 #\0))))
```

The next step is to be able to set bits. The easy part is finding the bit that we want to set. We can do the same thing as before. The more complicated part is setting the bits correctly. Setting a bit to 1 isn't too hard. You just need to `or` (or rather `bitwise-ior`) with the correctly shifted bit. So to see that 4th index:

```
/      \
00010001 <- bitvector
00001000 <- mask
00011001 <- updated bitvector
```

Setting a zero is a bit more complicated. Essentially, you want to and with all of the bits *except* the one to set to zero. You can do this by `xor`ing the 1 from the previous case with `0xFF`:

```
00001000 <- mask
11111111 <- 0xFF
11110111 <- xor'ed

/      \
00010001 <- bitvector
11110111 <- xor'ed mask
00010001 <- updated bitvector
```

To turn this all into code:

```scheme
; set a value in a bit vector
(define (bitvector-set! bv i v)
  (bytes-set!
   bv
   (quotient i 8)
   (cond
     [v
      ; set the value by or'ing with 1
      (bitwise-ior (bytes-ref bv (quotient i 8))
                   (arithmetic-shift 1 (remainder i 8)))]
     [else
      ; unset the value by anding with all 1s but a 0 at the interesting point
      (bitwise-and (bytes-ref bv (quotient i 8))
                   (bitwise-xor #xFF
                                (arithmetic-shift 1 (remainder i 8))))])))
```

A bit uglier than I'd like, workable. Let's try it out:

```scheme
> (define bv (make-bitvector 20))

> (bitvector->string bv 20)
"00000000000000000000"

> (bitvector-set! bv 4 #t)
> (bitvector-set! bv 8 #t)
> (bitvector-set! bv 9 #t)
> (bitvector-set! bv 10 #t)

> (bitvector->string bv 20)
"00001000111000000000"

> (bitvector-ref bv 7)
#f

> (bitvector-ref bv 8)
#t
```

All good. I did make one more helpful method to just toggle a bit. This could have been done directly with an `xor`, but it was easy enough to define in terms of `bitvector-ref` and `bitvector-set!`:

```scheme
; shortcut to toggle a bit in a bitvector
(define (bitvector-toggle! bv i)
  (bitvector-set! bv i (not (bitvector-ref bv i))))
```

And that's all there is to it. I've uploaded the code here: <a href="https://github.com/jpverkamp/small-projects/blob/master/racket-libraries/bitvector.rkt" title="bitvector source">bitvector source</a>