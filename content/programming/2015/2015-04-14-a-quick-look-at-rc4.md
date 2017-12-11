---
title: A Quick Look at RC4
date: 2015-04-14
programming/languages:
- Python
- Racket
programming/topics:
- Security
- Symmetric encryption
- TLS
---
In cryptography work, {{< wikipedia "RC4" >}} (Rivest Cipher 4) is well known as both one of the easiest to implement and fastest to run {{< wikipedia "symmetric encryption" >}} algorithms. Unfortunately, over time there have been a number of attacks on RC4, both in poorly written protocols (such as in the case of {{< wikipedia "WEP" >}}) or statistical attacks against the protocol itself.

Still, for how well it formed, it's an amazingly simple algorithm, so I decided to try my hand at implementing it.

<!--more-->

Basically, RC4 is what is known as a '{{< wikipedia "stream cipher" >}}', implying that each byte in the input message is encrypted individually (generally taking into account feedback from previous bytes). This runs counter to the perhaps more well known {{< wikipedia "block ciphers" >}} such as DES and AES, where bytes are instead encrypted together (although feedback between blocks is still of course possible).

The first step of the algorithm is to take your encryption key (a password or the like) and convert it into a sequence of bytes at least as long as your input. For RC4, this is done in two pieces. First, prepare the index:

```python
def rc4(key, msg):
    S = list(range(256))

    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]

    ...
```

Or in Racket:

```racket
(define (rc4 key msg)
  (define (mod256 n) (modulo n 256))

  (define permutation (make-bytes 256))
  (for ([i (in-range 256)])
    (bytes-set! permutation i i))

  (define (S i)
    (bytes-ref permutation i))

  (define (swap! i j)
    (let ([pi (bytes-ref permutation i)]
          [pj (bytes-ref permutation j)])
      (bytes-set! permutation i pj)
      (bytes-set! permutation j pi)))

  ; Key-scheduling algorithm
  (for/fold ([j 0]) ([i (in-range 256)])
    (let ([j (mod256 (+ j
                        (S i)
                        (bytes-ref key (modulo i (bytes-length key)))))])
      (swap! i j)
      j))

  ...)
```

I made the Racket version a little more verbose with helper functions, since I know I'll both be indexing the permutation and swapping values again in the next step. That's one of the reasons that I'll sometimes go for Python over Racket in on off scripts.

Still, relatively simple in both cases.

The next step is to turn that into a stream, essentially creating an infinite number generator. Luckily, both Python and Racket have generators, which are perfectly suited for this sort of thing (assuming in both cases that `S` / `permutation` are in scope from above):

```python
def rc4(key, msg):
    ...

    def prga():
        i = j = 0
        while True:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            yield S[(S[i] + S[j]) % 256]

    return prga # DEBUG
```

```racket
(define (rc4 key msg)
  ...

  ; Pseudo-random generation algorithm
  (define prga
    (generator ()
      (let loop ([i 1] [j (S 1)])
        (swap! i j)
        (yield (S (mod256 (+ (S i) (S j)))))
        (loop (mod256 (+ i 1)) (mod256 (+ j (S (+ i 1))))))))

  prng) ; DEBUG
```

Now that we have a stream, we can generate a few bytes and take a look if we wanted:

```python
>>> import binascii, itertools
>>> prga = rc4(b'Secret', b'Attack at dawn')
>>> print(binascii.hexlify(bytes(itertools.islice(prga(), 10))))
b'04d46b053ca87b594172'
```

```racket
(define (bytes->hex b*)
  (apply ~a (for/list ([b (in-bytes b*)])
        (~a (number->string (quotient b 16) 16)
            (number->string (modulo b 16) 16)))))

> (define prga (rc4 "Secret" "Attack at dawn"))
> (bytes->hex (apply bytes (for/list ([i (in-range 10)] [b (in-producer prga)]) b)))
"04d46b053ca87b594172"
```

Both of them the same? Good sign. Both matching the example on the Wikipedia page? Even better!

So, we have an infinite stream of bytes. What next?

Well, this is actually the crazy part: You just {{< wikipedia "xor" >}} them.

```python
def rc4(key, msg):
    ...

    return bytes(msgbyte ^ keybyte for msgbyte, keybyte in zip(msg, prga()))
```

```racket
(define (rc4 key msg)
  ...

  ; Encryption
  (apply bytes
    (for/list ([input-byte (in-bytes msg)] [key-byte (in-producer prga)])
      (bitwise-xor input-byte key-byte))))
```

And now we can encrypt!

```python
>>> print(binascii.hexlify(rc4(b'Secret', b'Attack at dawn')))
b'45a01f645fc35b383552544b9bf5'
```

```racket
> (bytes->hex (rc4 "Secret" "Attack at dawn"))
"45a01f645fc35b383552544b9bf5"
```

And decrypt!

```python
>>> rc4(b'Secret', rc4(b'Secret', b'Attack at dawn'))
b'Attack at dawn'
```

```racket
> (rc4 "Secret" (rc4 "Secret" "Attack at dawn"))
#"Attack at dawn"
```

Very cool. I'm really starting to see the appeal of RC4. A couple dozen lines of Python/Racket and you're encrypting. Bam. As mentioned, it's not really an algorithm you should use in encryption any more (the author has released a slightly more complicated algorithm called Spritz that works very similarly).

And that's it. If you'd like to see the entire code in one place (along with some fiddling in both cases to deal with Unicode keys/messages as well as pure bytes), it's on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/rc4.py">rc4.py</a>, <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/rc4.rkt">rc4.rkt</a>.

`7b82 c5cf 12c4 e168 8a4a 5cbe 9300`

:smile:
