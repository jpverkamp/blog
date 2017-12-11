---
title: Exploring parallelism in Racket with SHA-512 mining
date: 2014-02-16 14:00:30
programming/languages:
- Racket
- Scheme
programming/topics:
- Bitcoin
- Concurrency
- Dictionary
- Hashes
- Mathematics
- Parallelism
---
While I've been getting a fair few programming exercises from Reddit's <a href="http://www.reddit.com/r/dailyprogrammer">/r/dailyprogrammer</a>, more recently I've started following a few other sub-Reddits, such as <a href="http://www.reddit.com/r/programming">/r/programming</a> and <a href="http://www.reddit.com/r/netsec">/r/netsec</a>. While browsing the former, I came across this intriguing gem of a problem: <a tabindex="1" href="http://www.h11e.com/">HashChallenge: can you find the lowest value SHA-512 hash?</a>

<!--more-->

The basic idea is simple. Find the input string *s* such that the output SHA-512 hash is minimized. As an an example,

```bash
$ echo "Hello world" | shasum -a 512
81381f1dacd4824a6c503fd070577630...

$ echo "Even better" | shasum -a 512
77d8af6911952994e2d9597e6962ada1...
```

Of course, these aren't that great. At the very least we should be looking for hashes with a few leading zeros. Not to mention that this is something that should be downright trivial to automate. Let's start with a straight forward Racket script:

```scheme
; Mine for the lowest SHA-512 we can find
(define (mine)
  (define alphabet "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01234567890")
  (define hashes-tried 0)
  (define start-time (current-inexact-milliseconds))

  ; Store best values
  (define best-str #f)
  (define best-hash #f)

  ; Generate random values one at a time
    (let loop ()
      (define str   (random-string 16))
      (define bytes (string->bytes/utf-8 str))
      (define hash  (bytes->hex-string (sha512 bytes)))

      (set! hashes-tried (+ 1 hashes-tried))
      (when (or (not best-hash) (string<? hash best-hash))
        (set! best-str str)
        (set! best-hash hash)
        (print-timing 'main hashes-tried (/ (- (current-inexact-milliseconds) start-time) 1000) best-str best-hash))

      (loop)))
```

There are a few helper functions there (`random-string` and `print-timing`, you can see them in the full code on GitHub: <a href="https://github.com/jpverkamp/small-projects/tree/master/blog/mine-sha512">github/jpverkamp</a>), but those should be straight forward. The hashing itself is done with Greg Hendershott's <a href="https://github.com/greghendershott/sha/tree/master">`sha` library for Racket</a>, available via the new <a href="http://pkg.racket-lang.org/#[sha]">package manager</a>.

So, how does that do?

```bash
$ racket mine-sha512.rkt
main: 4ZRZ6R5eQO4GItzK -> 50ce827050c31fd0... (1.0 h @ 1.0 kh/s)
main: bGzP1aAnXjDEJ5tS -> 2a8e1803b7ac4b57... (16.0 h @ 16.0 kh/s)
main: 9IXIWuGDepUUSubp -> 048e4b1b9ae2e893... (20.0 h @ 20.0 kh/s)
main: nwVB9KFI0ieHm0n4 -> 007704acb8e01bcf... (105.0 h @ 52.5 kh/s)
main: WeQFXLb3UhwyaHRr -> 000b17576f358405... (364.0 h @ 91.0 kh/s)
main: D19naE3qFtrKT6Lt -> 000707066075fce0... (6.0 kh @ 100.7 kh/s)
main: 4PQKs7crKnQTBjfs -> 00018fe9e134c366... (11.7 kh @ 113.6 kh/s)
main: NZS717BXvT0ErzSR -> 0000ed34ec5c0222... (120.5 kh @ 131.1 kh/s)
main: 3QuXbtG0xlRaDKqV -> 000005fb0ac4a407... (2.7 Mh @ 133.2 kh/s)
```

Since it only prints a line when it finds a new best hash, output can be a little chaotic at best, but at the very least this gives us a pretty good baseline. We managed to find a hash with 5 leading zeros and are running at about 133.2 kh/s. Nowhere near what most ASIC bitcoin miners <a href="https://en.bitcoin.it/wiki/Mining_hardware_comparison#ASIC">claim to be able to do</a>[^1], but not terrible for a pure CPU miner.

Let's do better.

The next idea would be to use Racket's threads. Going in to it, I already know that this isn't going to buy us much[^2], but it's an easy enough tweak.

First, pull out the `hashes-tried`, `best-str`, and `best-hash` variables so all threads can access them. Then, create a wrapper function that will fire off the right number of threads:

```scheme
; Mine with multiple threads concurrently
(define (mine-all thread-count)
  (define threads
    (for/list ([i (in-range thread-count)])
      (thread (thunk (mine i)))))
  (map thread-wait threads))
```

This way we also get to know which thread found the new best value (although strictly speaking that's not necessary):

```bash
$ racket mine-sha512-threads.rkt 8
7: OsultHDT905n5mmo -> c0b8ad26ae6472f8... (1.0 h @ 62.5 h/s)
7: pEyhYUxIM74peJxi -> 13c7391822e728c3... (3.0 h @ 187.5 h/s)
7: jPMHHOwwJeGe7bqF -> 0045856cdcfbe797... (10.0 h @ 625.0 h/s)
7: TE2nEcH10rcWefsn -> 003e888a92cd8809... (1.0 kh @ 43.7 kh/s)
7: WTGTqrOpl2x1Czi1 -> 0024448bf70a1247... (1.1 kh @ 49.5 kh/s)
6: EMhqI5ngPwiQr4gK -> 000ae12edd827730... (2.8 kh @ 78.0 kh/s)
5: Gftv6FPZwVF4xTct -> 000031b56d17483b... (3.8 kh @ 88.7 kh/s)
1: gDNLGB6Dzlp9YVBj -> 00002a7fd4a81c8d... (287.5 kh @ 143.2 kh/s)
1: G0F4FLKwPNbUzQGO -> 0000117e20b56196... (646.2 kh @ 144.6 kh/s)
0: 0hmB7jnocqRMuSxu -> 00000a1a4b05d9b7... (2.9 Mh @ 144.8 kh/s)
7: PM59fjq5g2huYTEN -> 000004cb6fd3fe14... (4.8 Mh @ 143.8 kh/s)
4: 4WzSTKXi540JlyJL -> 000004713d42ec3b... (5.1 Mh @ 143.7 kh/s)
```

So we have a slight speed up. I guess that's something. The problem is that we're still actually only running in a single process on a single processor. With four cores, that's something of a waste. Unfortunately though, we aren't going to be able to do much better than that with threads. We need something a little more powerful:

{{< doc racket "Places" >}}

The basic idea of places is:

> {{< doc racket "Places" >}} enable the development of parallel programs that take advantage of machines with multiple processors, cores, or hardware threads.

Sounds like exactly what we want. Unfortunately, that extra power comes with a bit of extra cost. No longer can we share variables directly between the various threads of the program, but rather now we have to communicate explicitly, using {{< doc racket "place channels" >}}. The basic idea I have is to split the work up into *n* places. For each place, run two threads: a hashing thread and a feedback thread. The hashing thread is pretty much the mining function we've seen all along.

The feedback thread, on the other hand, will periodically send messages back to the main program relaying how much progress we've made and any new hashes we've found. Then, the main program can compare that to the other place's results and update with the overall best hash.

Starting with the new mining function:

```scheme
; Create a place that will mine for new low hashes
(define (mine id)
  (place me
    ; Local best values
    (define hashes-tried 0)
    (define best-str #f)
    (define best-hash #f)

    ; Thread to periodically send back new best values
    (thread
      (thunk
        (let loop ()
          (place-channel-put me hashes-tried)
          (place-channel-put me best-str)
          (place-channel-put me best-hash)
          (sleep (* (random) 10.0))
          (loop))))

    ; Look for new values
    ...))
```

Fairly straight forward. The macro `place` at the top actually handles all of the work of creating a new place. `me` will be used to identify the automatically created channel we use a bit later to send messages on. Each time we send messages, we send three values: how many hashes this place has personally tried and the best string/hash pair. So of course, the main program will have to be listening for these three values from each place in turn:

```scheme
; Run multiple mining places in parallel and sync between them
(define (mine-all thread-count)
  ; Global best values
  (define start-time (current-inexact-milliseconds))
  (define best-str #f)
  (define best-hash #f)

  ; Create places
  (define places
    (for/list ([i (in-range thread-count)])
      (mine i)))

  ; Loop through those, getting their best values in time
  (let loop ()
    (for ([id (in-naturals)]
          [p (in-list places)])
      (define hashes-tried (place-channel-get p))
      (define str (place-channel-get p))
      (define hash (place-channel-get p))

      (when (or (not best-hash) (and hash (string<? hash best-hash)))
        (define estimated-hashes (* hashes-tried thread-count))
        (set! best-str str)
        (set! best-hash hash)
        (print-timing id estimated-hashes (/ (- (current-inexact-milliseconds) start-time) 1000) best-str best-hash)))
    (loop)))
```

There is a potential inefficiency here, in that we go round robin through the places asking each in turn for their best hash. Because they wait a random amount of time (up to 10 seconds) between reports, it could be a bit before we actually report a new lowest hash[^3]. In fact, it may even be out of date by then. Still, it's a reasonable enough count, especially if you're going to be running the program for a while.

So with that being said, the first thing to try would be a single place. Theoretically, that should give us the same performance as the original program (maybe minus a bit for the channel):

```bash
$ racket mine-sha512-places.rkt 1
0: 38H0DQxOWh0swGlq -> 000581b5f1373c77... (2.1 kh @ 5.4 kh/s)
0: TZdL5yWiiMb6WFVV -> 00006cc7dac2d460... (252.4 kh @ 116.6 kh/s)
0: 0AnndUtx0XmNfX9a -> 00000893ee217109... (1.3 Mh @ 136.5 kh/s)
0: bGh0LDfnwCiSIb95 -> 000001e204acff0c... (4.4 Mh @ 140.2 kh/s)
0: JoWy6CXotik87OWh -> 0000010fe4646f6f... (6.5 Mh @ 140.7 kh/s)
0: iS6rIH4kClxc0SdF -> 000000ecdcc2cc1e... (16.0 Mh @ 141.3 kh/s)
```

Well that's not bad at all. If anything, it's a little faster[^4].

Now, let's really let it go. I have 4 cores, so let's try 4 places:

```bash
$ racket mine-sha512-places.rkt 4
0: J1vkvS8s1WJJ7CUt -> 003abedaf7fcdab7... (13.2 kh @ 27.6 kh/s)
1: 383Xt0hLlAl0JZWO -> 00098c00746f1807... (11.5 kh @ 24.0 kh/s)
0: 7EmH4gk7T2aecSph -> 0000060d3d0f9ddf... (3.7 Mh @ 505.7 kh/s)
0: XxeeMSUlYWPzrUh1 -> 00000494b2eccdbf... (5.5 Mh @ 519.9 kh/s)
3: 7a5MD2k0uILVj8aB -> 000002037fce01ec... (7.2 Mh @ 520.5 kh/s)
1: A3HTACsXRI5QkwWU -> 000001de799bfeaa... (31.9 Mh @ 529.1 kh/s)
```

That's a lot more like it. And at a roughly 3.75x speedup over a single place, pretty much exactly what {{< wikipedia "Amdal's law" >}} would expect we'd be able to get in speedup. If we try it with 8, we don't do any better (a brief spike, but overall it's actually worse):

```bash
$ racket mine-sha512-places.rkt 8
0: JRxl4puWgUCIBvZ1 -> 00016f513c85da0e... (49.6 kh @ 54.8 kh/s)
4: LU5sj3zJmG30w4O3 -> 000026edd66b3458... (13.4 kh @ 11.0 kh/s)
1: AvFOADpeY1vn0q5z -> 000018a5d4019643... (2.0 Mh @ 247.9 kh/s)
2: wyIvWO5nYh7MgbTR -> 00000658bae50546... (4.6 Mh @ 452.7 kh/s)
7: ekrIcXa8CVmXKmVr -> 000004e231c16d72... (5.1 Mh @ 168.4 kh/s)
1: 1mTOnp0weetWHLbp -> 00000270cab144e8... (24.0 Mh @ 736.0 kh/s)
0: 7GG6p6sK1e4EvbzV -> 0000013d126816a5... (34.2 Mh @ 459.2 kh/s)
```

Of course that's still nothing on the record hashes so far. In the contest running <a href="http://www.h11e.com/">here</a>, the best as of my writing is `0000000003aeefb5...` A bit of a way to go, that.
Still, it's an interesting problem--and a nice excuse to learn a little more about places and channels in Racket. I've used them before, but I think they made a little more sense this time around.

If you'd like to see the entire code for today's post, it's on GitHub: <a href="https://github.com/jpverkamp/small-projects/tree/master/blog/mine-sha512">github/jpverkamp</a>

[^1]: Those are generally measured in Mh/s
[^2]: Threads give us {{< wikipedia page="Concurrency (computer science)" text="concurrency" >}} in Racket, not {{< wikipedia page="Parallel computing" text="parallelism" >}}
[^3]: Averaging 5 seconds times the number of places in fact
[^4]: Which is probably just an artifact of the timing. There's no particular reason this code should actually be faster.
