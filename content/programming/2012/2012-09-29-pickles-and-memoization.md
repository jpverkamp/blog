---
title: Pickles and memoization
date: 2012-09-29 14:00:47
programming/languages:
- Python
---
[[wiki:Memoization]]() (yes, that's the correct word) is a method of optimization in computer science where the first time you run a function you cache the result. After that, rather than re-doing the work, you can simply return the previous result. It's not always perfect as you're trading time for space.

<!--more-->

Let's start with a simple enough example, the most straight forward way (that you're not supposed) to write a function that calculates [[wiki:Fibonacci number|Fibonacci numbers]](). Each call depends on two previous calls so F<sub>n</sub> depends on F<sub>n-1</sub> and F<sub>n-2</sub> which in turn depend on F<sub>n-2</sub>, F<sub>n-3</sub>, F<sub>n-3</sub>, and F<sub>n-4</sub>. Note the duplication on F<sub>n-3</sub>. Without a smarter algorithm, such duplication is only going to get worse. For example, calculating F<sub>35</sub> (as below) will take a full 29,860,703 calls to Fibonacci while only depending on 35 values.

```python
def fib(n): return 1 if n <= 1 else fib(n - 1) + fib(n - 2)
```

This will give us the correct value of F<sub>35</sub> = 14930352 in 6.20 seconds. Let's see if we can do better.

```python
from pickled import pickled

@pickled
def fib(n): return 1 if n <= 1 else fib(n - 1) + fib(n - 2)
```

We get the same answer, but this time it only calls Fibonacci 36 times, once for each value. All together, it only takes 0.04 seconds, most of which is disk access (I'm using the file system as a cache, see below). And even better, all you need is an import and the `@pickled` decorator.

Magic! (Or just smarter code.)

So how does it work?

```python
import os
try:
    import cpickle as pickle
except:
    import pickle

def pickled(f):
    def new_f(*args, **kwargs):
        compressed = ''
        if len(args) > 0:
            compressed = '_' + '_'.join([str(arg)[:10] for arg in args])
        if len(kwargs) > 0:
            compressed += '_' + '_'.join([(str(k)+str(v))[:10] for k,v in kwargs])

        filename = '%s%s.pickle' % (f.__name__, compressed)

        if os.path.exists(filename):
            pickled = open(filename, 'rb')
            result = pickle.load(pickled)
            pickled.close()
        else:
            result = f(*args, **kwargs)
            pickled = open(filename, 'wb')
            pickle.dump(result, pickled)
            pickled.close()

        return result

    new_f.__name__ = f.__name__
    new_f.__doc__ = f.__doc__

    return new_f
```

Basically, we're using files on disk (where the file names are based on the arguments to the function) to cache the results, generating one file per function call. Definitely not optimal, but it works well enough for some cases.

One interesting side effect is that if you run the function again, it just has to read it directly from disk. So running it again takes a completely negligible amount of time. So it actually makes a decent system for persistence.

Also Python's decorators are awesome. That is all.

You can download the full source <a href="https://github.com/jpverkamp/small-projects/blob/master/python-libraries/pickled.py" title="pickled source">here</a>.