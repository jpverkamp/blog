---
title: Parallel BF
date: 2012-12-31 22:45:11
programming/languages:
- Brainf**k
- Racket
- Scheme
programming/sources:
- PLT Games
programming/topics:
- Esolangs
---
Getting a bit close to the deadline, but I think I have something that's pretty interesting. Basically, it's the same BF interpreter that I wrote about [yesterday]({{< ref "2012-12-30-a-brainf-k-interpreter.md" >}}) with four additional commands:


| & | Spawn a new thread; set the current cell to 0 in the parent and 1 in the child |
|---|--------------------------------------------------------------------------------|
| ~ |                            Kill the current thread                             |
| ! |            Send a ping on the channel specified by the current cell            |
| ? |          Wait for a ping on the channel specified by the current cell          |


<!--more-->

Originally, the idea was the keep the threads in sync, running only a single step on each in turn, but in the end I decided just to directly go with Racket's `thread`s both for ease of implementation and because it more closely matches what I'm actually trying to do. 

If you'd like to see full source code, you can do so <a href="https://github.com/jpverkamp/pbf/blob/master/pbf.rkt" title="GitHub: pbf">on GitHub</a>. Otherwise, here are the new sections:

First, we have the new instruction `&amp;` that is designed to spawn a new thread:

```scheme
; spawn a new thread, set current cell to 0 in the parent and non-0 in the child
[(#\&)
 ; spawn the child process
 (thread
  (lambda () (step (+ pc 1) tape-left 1 tape-right)))

 ; step the parent process
 (step (+ pc 1) tape-left 0 tape-right)]
```

That's one thing that I like about the provided `thread`s, all you have to do is pass it a thunk and it does the rest. So we'll spawn one process in a separate thread with 1 in the current cell and take a step while at the same time taking a step in the original thread. And that's it! The built in functionality will handle everything else for us. 

Next, how do we kill off threads? That's even easier. Since we have the large `case` statement that's dealing with processing the input, all we have to do is break out of it (by returning `void` in this case):

```scheme
; kill the current thread
[(#\~)
 (void)]
```

Now for the communication between threads. Optimally, I'd like to have something that could actually send messages, but I couldn't figure out a good way to do that while only having a single variable at a time. Perhaps I could just send/receive the current cell? We'll see. 

In any case, the model that I settled on is useful for synchronizing the threads. Basically, you can send a ping with `!` or wait for one with `?`. 

But how does that work? First we need the channels of communication. I used a shared mutable hash:

```scheme
; control communication on channels
(define channels (make-hash))

; send a ping on a given channel
(define (ping i)
  (hash-set! channels i #t))

; wait for a ping on a given channel
; current a spinlock :(
(define (pong i)
  (let loop ()
    (if (hash-ref channels i #f)
        (hash-remove! channels i) 
        (loop))))
```

This way `pong` will block until it receives a message from another thread. there are some potential issues in that `pong` isn't actually atomic so you could have two threads receive the same ping or not, non-deterministically. But that's half the fun of a Turing Tarpit isn't it? :smile:

With that, the code for `!` and `?` is straight forward:

```scheme
; send a ping on a given channel
[(#\!)
 (ping tape-cell)
 (step (+ pc 1) tape-left tape-cell tape-right)]

; receive a ping on a given channel
[(#\?)
 (pong tape-cell)
 (step (+ pc 1) tape-left tape-cell tape-right)]
```

And that's all there is to it. Now you can BF in parallel!

But what's it actually useful for?

Well, consider this example:

```java
&[     spawn thread 1 (echo +1)
 +     set cell 0 to 1 (to ID the thread)
 >>+   set cell 2 to 1
 <,    read into cell 1
 [     while not EOF:
  +.    add 1 and echo
  >+!   set cell 2 to 2 and send a ping on 2
  -?    set cell 2 to 1 and wait for a ping on 1
  <,    read into cell 1
 ]
 ~     kill this thread
]

&[     spawn thread 2
 ++    set cell 0 to 2 (to ID the thread)
 >>++? set cell 2 to 2 and wait for a ping on 2
 <,    read into cell 1
 [     while not EOF:
  -.    sub 1 and echo
  >-!   set cell 2 to 1 and send a ping on 1
  +?    set cell 2 to 2 and wait for a ping on 2
  <,    read into cell 1
 ]
 ~     kill this thread
]
```

What this will actually do is act as a close cousin to the cat program from yesterday. Instead of a single thread though, here we spawn two. The first will read input and add one to it before echoing. The second will subtract one. Using `!` and `?`, we'll make sure to alternate between the two. Yes, this could easily have been written without threads, but it was a good test to make sure I had everything working.

Here's an example:

```scheme
> (current-i/o-mode 'numeric)
> (pbf (file->string "split-cat.pbf"))
2 4 6 8 10
3 3 7 7 11
```

Even more fun, how about Hello World done in parallel? Essentially, we can have one thread for upper case letters, one for lower case, and one for the rest. That way we can move around and get everything read all at the same time:

```java
the goal:
 thread 0 outputs 'H' and sends 1
 on 1 thread 1 outputs 'ello' and sends 2
 on 2 thread 2 outputs ' ' and sends 3
 on 3 thread 0 outputs 'W' and sends 4
 on 4 thread 1 outputs 'orld' and sends 5
 on 5 thread 2 outputs bang

&[-         spawn thread 0 (for H and W)
 >          go to cell 1
 +++++++++  set cell 1 to 9
 [          loop while cell 1 is not 0:
  <++++++++  add 8 to cell 0
  >-         subtract 1 from cell 1
 ]
 <.         output cell 0 (9 * 8 = 72 = 'H')
 >+!        send a ping on 1
 ++         set cell 2 to 3
 [          loop while cell 1 is not 0:
  <+++++     add 5 to cell 0
  >-         subtract 1 from cell 1
 ]
 +++?      wait for a ping on 3
 <.        output cell 0 (72 + 3 * 5 = 87 = 'W')
 >+!        send a ping on 4
 ~          kill this thread
]

&[-         spawn thread 1 (for 'ello' and 'orld')
 >+++++
  +++++     add 10 to cell 1
 [          while cell 1 is not 0:
  <+++++
   +++++    add 10 to cell 0
  >-        subtract 1 from cell 1
 ]
 <+         add 1 to cell 0
 >+?        wait for a ping on 1
 <.         output cell 0 (10 * 10 + 1 = 101 = 'e')
 ++++++..   add 7 to cell 0 (for 108 = 'l') and output twice
 +++.       add 3 to cell 0 (for 111 = 'o') and output
 >+!        send a ping on 2
 ++?        wait for a ping on 4
 <.         output cell 0 ('o')
 +++.       add 3 and output (114 = 'r')
 ------.    subtract 6 and output (108 = 'l')
 --------.  subtract 8 and output (100 = 'd')
 >+!        send a ping on 5
 ~          kill this thread
]

&[-         spawn thread 2 (for ' ' and bang)
 >++++      set cell 1 to 4
 [          while cell 1 is not 0:
  <++++++++  add 8 to cell 0
  >-         subtract 1 from cell 1
 ]
 ++?        wait for a ping on 2
 <.         output cell 0 (4 * 8 = 32 = ' ')
 >+!        send a ping on 3
 <+         add 1 to cell 0
 >++?       wait for a ping on 5
 <.         output cell 0 (32 + 1 = 33 = '!')
 ~          kill this thread
]
```

Check it out:

```scheme
>(current-i/o-mode 'unicode)
> (pbf (file->string "hello.pbf"))
Hello World!
```

And that's that. You can see the entire project on GitHub <a href="https://github.com/jpverkamp/pbf" title="GitHub: jpverkamp/pbf">here</a> or the competition from <a href="http://www.pltgames.com/competition/2012/12" title="PLT Games Competition December 2012">PLT Games here</a>.

This was actually pretty fun. I think I'm going to have to try a few other variants in the future.
