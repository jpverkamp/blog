---
title: A "one" line echo server using let in Racket
date: 2014-11-13
programming/languages:
- Racket
- Scheme
programming/topics:
- Networks
---
A recent post on Reddit caught my attention: <a href="https://www.reddit.com/r/Python/comments/2m6d4z/a_one_line_echo_server_using_let_in_python/">A “One” Line Echo Server Using “let” in Python</a> (<a href="http://sigusr2.net/one-line-echo-server-using-let-python.html">original article</a>). The basic idea is that you can use Python's `lambda` with default arguments as a `let`, which in turn allows you to write a simple {{< wikipedia "echo server" >}} in ~~one line~~ a nicely functional style.

<!--more-->

To start with, here is their original code:

```racket
import socket
import itertools

(lambda port=9000, s=socket.socket(socket.AF_INET, socket.SOCK_STREAM):
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) == None and
      s.bind(('', port)) == None and
      s.listen(5) == None and
      list(map(lambda c:
                  c[0].sendall(c[0].recv(1024)) and
                  c[0].close(),
               (s.accept() for _ in itertools.count(1)))))()
```

It's certainly not very Pythonic, but there are a few neat tricks in there:


* Using `lambda` with default arguments to define things
* Using `and` to sequence function calls
* Using list comprehension to handle the response threads


It got me thinking though, what would the same sort of code look like in Racket?

Well, one of the draws Racket advertises (rightfully so) on its <a href="http://racket-lang.org">home page</a> is that it comes <a href="http://docs.racket-lang.org/">batteries included</a>. That means that if you're using {{< doc racket "#lang racket" >}}, you get a bunch of useful functions for TCP built in. Let's start with a fairly direct translation:

```racket
(let ([s (tcp-listen 9000)])
  (sequence->list
   (sequence-map
    (λ (in+out) (thread (thunk (apply copy-port in+out))))
    (in-producer (thunk (call-with-values (thunk (tcp-accept s)) list))))))
```

Okay, so that looks really weird. But it's a fairly straight forward translation. A few of the lines got folded into the {{< doc racket "tcp-connect" >}} call and the list comprehension became a {{< doc racket "in-producer" >}} {{< doc racket "sequence" >}}. It's kicked off via {{< doc racket "sequence-map" >}} and forced to run to termination (which will never happend) with {{< doc racket "sequence->list" >}}. Unfortunately, it has the same problem that the original Python code does. Since we're constructing a list, we'll eventually run out of memory.

One interesting addition it does that the Python version didn't is that it both allows for multiple lines (the Python version would read one packet and hang up) and any amount of data. I've never actually used the {{< doc racket "copy-port" >}} function before. It's really cool!

If we broaden our definition of "one" line a little more to allow {{< doc racket "for" >}} sequences (which aren't really that different under the hood), we can clean it up a bit to this:

```racket
(let ([s (tcp-listen 9000)])
  (for ([(in out) (in-producer (thunk (tcp-accept s)))])
    (thread (thunk (copy-port in out)))))
```

This is especially nice, since {{< doc racket "in-producer" >}} and {{< doc racket "for" >}} work together to deal with the multiple values from {{< doc racket "tcp-accept" >}}. Very clean.

Heck, if you want to get a little less clear about it, you can actually fold the `let` into the `for`:

```racket
(for* ([s (in-value (tcp-listen 9000))]
       [(in out) (in-producer (thunk (tcp-accept s)))])
  (thread (thunk (copy-port in out))))
```

This works because `for*` is actually a nested loop. So in the outer loop, it runs over the single value of the open socket. The inner loop then runs forever, accepting new incoming connections.

Actually, I may have to put this in my quick-scripts toolbox. There are a fair few times when writing networking clients that having a dead simple echo server could come in handy.
