---
title: Hash Tables With Open Addressing
date: 2012-08-29 14:00:26
programming/languages:
- Scheme
programming/sources:
- Programming Praxis
---
Another day, another post from [here](https://github.com/jpverkamp/small-projects/blob/master/chez-libraries/hash.ss).

Okay, first, some administrative detail. First, we have to set up the library (we're important the standard Chez Scheme library) and the data structure that we're going to use internally. The nice thing about `define-record` is that it makes a bunch of functions for us, like the constructor `make-:hash:` and the accessors `:hash:-f`, `:hash:-nul`, `:hash:-vals`, etc. 

```scheme
(library (hash)
  (export make-hash hash-ref hash-set! hash-unset! hash->list)
  (import (chezscheme))

  (define-record :hash: (f nul del keys vals))
```

Next up, we want a function that will set up a hash. I went with the abstraction that you pass the hashing function in here and it's stored with the hash record rather than passing it around all over the place. The nul and del symbols are also created here, gensym'ed to be unique<sup>1</sup>. The hash function is also wrapped here to force all generated keys to be in the proper range.

```scheme
; given a hash function and a size for the table, create a hash
(define (make-hash hash-function size)
  (let ([nul (gensym)])
    (make-:hash: 
      (lambda (key)
        (mod (hash-function key) size))
      nul
      (gensym)
      (make-vector size nul)
      (make-vector size nul))))
```

Next, our first helper function. I want to be able to unpack all of the parts of a `:hash:` structure, which I can do with this nice bit of code and the helper of multiple value returns. Behold the power of Scheme!

```scheme
; unpack a :hash:
(define (*unpack h)
  (values 
    (:hash:-f h) (:hash:-nul h) (:hash:-del h)
    (:hash:-keys h) (:hash:-vals h)))
```

Our second helper. This one is the core of pretty much all of the rest of the functions. Basically, we want to turn a key into an index. If the key is in the hash, this should be the index into the `keys` and `vals` for that key. If the key isn't, this should be the first location currently marked as either `nul` or `del` after that point. If the hash is full when you try to look up a hash that isn't already in it, then you'll get a nice error. 

```scheme
; convert a hash into an index
; start at the hashed index and look for either that key or nul
; error (hash is full) if we loop
; set del? to return a del? index
(define (*get-index h k del?)
  (let-values ([(f nul del ks vs) (*unpack h)])
    (let ([i0 (f k)])
      (let loop ([i i0] [fst #t])
        (cond
          [(and (not fst) (= i i0)) (error 'hash "hash is full")]
          [(equal? (vector-ref ks i) k) i]
          [(equal? (vector-ref ks i) nul) i]
          [(and del? (equal? (vector-ref ks i) del)) i]
          [else (loop (mod (+ i 1) 1000) #f)])))))
```

Once the helper is set up, it makes writing things like `hash-ref` much easier. Just find the index. If they key matches, return the value; otherwise, return an error.

```scheme
; get the value associated with a key k out of the hash h
; error if they key has not been set
(define (hash-ref h k)
  (let-values ([(f nul del ks vs) (*unpack h)])
    (let ([i (*get-index h k #f)])
      (cond
        [(equal? (vector-ref ks i) nul)
         (error 'hash "key not set")]
        [else
         (vector-ref vs i)]))))
```

Even easier is the mutator for binding a key and a value. Since the `*get-index` function returns either the index of the item if it already exists or the first available index, you can just use that and then set the key and value. Done. Bam.

```scheme
; get the value associated with key k out of the hash h
(define (hash-set! h k v)
  (let-values ([(f nul del ks vs) (*unpack h)])
    (let ([i (*get-index h k #t)])
      (vector-set! ks i k)
      (vector-set! vs i v))))
```

Same for unsetting values. Just set the key and value to `del`. Technically, we don't have to set the value as a value associated with `key = del` will never show up, but we might as well.

```scheme
; remove a given key from the hash
(define (hash-unset! h k)
  (let-values ([(f nul del ks vs) (*unpack h)])
    (let ([i (*get-index h k #t)])
      (vector-set! ks i del)
      (vector-set! vs i del))))
```

Finally, a nice helper function to convert a hash into an association list. Pretty straight forward.

```scheme
; convert a hash into a list of key, value pairs
(define (hash->list h)
  (let-values ([(f nul del ks vs) (*unpack h)])
    (let loop ([i 0])
      (cond
        [(= i (vector-length ks)) '()]
        [(or (equal? (vector-ref ks i) nul)
             (equal? (vector-ref ks i) del))
         (loop (+ i 1))]
        [else
         (cons 
           (cons (vector-ref ks i) (vector-ref vs i))
           (loop (+ i 1)))]))))
```

And then the inverse:

```scheme
; convert a hash into a list of key, value pairs
(define (hash->list h)
  (let-values ([(f nul del ks vs) (*unpack h)])
    (let loop ([i 0])
      (cond
        [(= i (vector-length ks)) '()]
        [(or (equal? (vector-ref ks i) nul)
             (equal? (vector-ref ks i) del))
         (loop (+ i 1))]
        [else
         (cons 
           (list (vector-ref ks i) (vector-ref vs i))
           (loop (+ i 1)))]))))
```

Also, I wanted to make the printout a little nicer. Instead of printing out the hash function and `nul` and `del` values, just print out the association list.

```scheme
; custom writer for the hash
(record-writer (type-descriptor :hash:smile:
  (lambda (r p wr)
    (display "#[hash " p)
    (wr (hash->list r) p)
    (display "]" p)))
```

All together, we have a nice hashing library. Let's try it out! I'm going to use Chez Scheme's built in `string-hash` for the hashing function. Let's start with a 100 item hash.

```scheme
~ (import (hash))

~ (define h (make-hash string-hash 100))

~ h
 #[hash ()]
```

Now, we'll add a few keys:

```scheme
~ (hash-set! h "cat" "dog")

~ (hash-set! h "thunder" "storm")

~ (hash-set! h "alpha" "beta")

~ h
 #[hash (("thunder" "storm") ("cat" "dog") ("alpha" "beta"))]
```

Delete one and reset another:

```scheme
~ (hash-unset! h "cat")

~ (hash-set! h "thunder" "stone")

~ h
 #[hash (("thunder" "stone") ("alpha" "beta"))]
```

Finally, test `hash->list` and `list->hash`. The `list->hash` also tests collisions as everything hashes to the same thing. (Isn't that an awesome hashing function?)

```scheme
~ (hash->list h)
 (("thunder" "stone") ("alpha" "beta"))

~ (define h2 (list->hash (lambda (x) x) 5 '((0 zero) (1 one) (5 five))))

~ (hash-unset! h2 1)

~ (hash-set! h2 2 'two)

~ h2
 #[hash ((0 zero) (5 five) (2 two))]
```

Anyways, that's what I have. You can download the entire code [here](https://github.com/jpverkamp/small-projects/blob/master/chez-libraries/hash.ss).

<sup>1</sup> unique enough for our purposes anyways
