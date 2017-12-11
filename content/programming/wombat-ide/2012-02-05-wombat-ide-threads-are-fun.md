---
title: Wombat IDE - Threads are *fun*
date: 2012-02-05 04:55:57
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
Threads can get all sorts of interesting sometimes. And fun to debug. Essentially, whenever the user would restart the Petite process (using the Stop button) a new output thread would be spawned. There wasn't any problem with the output being duplicated or lost--I already had locking in place to prevent that--but what would happen is that the threads would interleave the output, scrambling output nicely.

<!--more-->

Things like this got all sorts of possible:

Expected:

```
~ (let loop ([i 0])
    (when (< i 10)
      (display i)
      (loop (+ i 1))))
0123456789
```

Actual:

```
~ (let loop ([i 0])
    (when (< i 10)
      (display i)
      (loop (+ i 1))))
0123<span style="color: #ff0000;">46</span>789<span style="color: #ff0000;">5</span>
```

(And it only got worse from there.)

It took a bit longer than I would have liked to track that down, but I finally managed to fix it so that only a single thread would be started no matter how many times the user restarts Petite.