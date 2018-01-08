---
title: "AoC 2017: Library Functions"
date: 2017-12-01 00:00:02
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Command line
series:
- Advent of Code 2017
---
As mentioned in the [main post]({{< ref "2017-12-01-advent-of-code-year-3.md" >}}), I'm structuring my solutions a bit differently this year. Rather than repeating the same relatively lengthy header in each function, we're going to have a few shared files that can be imported or used for every problem.

<!--more-->

Specifically, I have a trio of shared files not directly related to any particular day:

- [lib.py](https://github.com/jpverkamp/advent-of-code/blob/master/2017/lib.py) - a shared library that can be used my multiple files; this will handle command line parameters, user input from files, logging, and have a few helper functions

To start out with, we have the a few basic parameters that are available to any day:

```python
_arg_parser = argparse.ArgumentParser()
_arg_parser.add_argument('--part', type = int, default = 1, choices = (1, 2))
_arg_parser.add_argument('--debug', action = 'store_true')

_argument_groups = {}

_DEBUG_MODE = False

def add_argument(*args, **kwargs):
    _arg_parser.add_argument(*args, **kwargs)

def param(name, cache = {}):
    '''
    Get parameters from the command line by name.
    arg('input') will generate lines of input from fileinput
    '''

    global _DEBUG_MODE

    if not cache:
        cache['args'], cache['unknown'] = _arg_parser.parse_known_args()

        if cache['args'].debug:
            _DEBUG_MODE = True

    if name == 'input' and not hasattr(cache['args'], 'input'):
        return fileinput.input(cache['unknown'])
    else:
        return getattr(cache['args'], name)
```

Mostly, this wraps {{< doc python argparse >}}, but it also lets us get parameters without having to worry about the underlying implementation. In addition, we can use this for logging:

```python
def log(message, *args, **kwargs):
    if _DEBUG_MODE:
        print(message.format(*args, **kwargs))
```

This is faster than Python's built in {{< doc python logging >}} function since it doesn't even try to log if we're not in `_DEBUG_MODE`.

Next, we have a standard `lib.input()` function that will automatically wrap {{< doc python fileinput >}}. That's a nice library that will make Unix style file input easy. You can either read from `stdin` without specifying anything, or you can can specify one or more files to read from instead. This is all handled automatically, including stripping all whitespace / just newlines and skipping (Python style) comments. All a specific day has to do is something akin to `for line in lib.input()`.

Last but not least (there will be more in specific days), I have a general math function:

```python
def math(expression, variables):
    '''Safely evaluate a mathematical expression with the given variables.'''

    if re.match(r'[^0-9a-z+\-*/ ]', expression):
        raise Exception('Unsafe expression: {}'.format(expression))

    # TODO: Make this actually safe.

    return eval(expression, globals(), variables)
```

This will 'safely' evaluate a basic mathematical expression. It can only contain numbers, variable names, and the four basic operators (`+`, `-`, `*`, `/`), but it's useful from time to time to be able to evaluate mathematical expressions. It came up a few times last year.

The only remaining annoyance I have is that it's not super easy to import a Python file from one level above where you are running. I finally settled on this:

```python
import sys; sys.path.insert(0, '..'); import lib
```

It's ugly, but it works. Perhaps I'll figure out something more elegant in the future? Running from one level up would work, but that's not something I want to do just yet.

Next up, we have something like a test suite:

- [test-cases.yaml](https://github.com/jpverkamp/advent-of-code/blob/master/2017/test-cases.yaml) - a list of commands that can be run to print out my particular answers for every day along with timing information
- [run-all.py](https://github.com/jpverkamp/advent-of-code/blob/master/2017/run-all.py) - the script that actually loads `test-cases.yaml` and runs it

That will let me run either specific days:

```python
$ python3 run-all.py day-01

day-01  python3 ahctpat.py input.txt    0.05250382423400879     1102
day-01  python3 ahctpat.py input.txt --function "size // 2"     0.055709123611450195    1076
```

Or everything:

```python
$ python3 run-all.py

day-01  python3 ahctpat.py input.txt    0.05324125289916992     1102
day-01  python3 ahctpat.py input.txt --function "size // 2"     0.05552506446838379     1076
day-02  python3 check-it.py input.txt --part 1  0.05425620079040527     51139
day-02  python3 check-it.py input.txt --part 2  0.05429983139038086     272
day-03  python3 spiraly.py 347991 --part 1      0.5735530853271484      480
day-03  python3 spiraly.py 347991 --part 2      0.06040596961975098     349975
day-04  python3 password-validator.py input.txt 0.059782981872558594    337
day-04  python3 password-validator.py input.txt --no-anagrams   0.06075477600097656     231
...
```

It gives me the day, the command I ran, how long it took to run (in seconds), and the output I would submit to solve the puzzle. It's nice to have it all in one place.

And... that's about it for now.
