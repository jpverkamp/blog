---
title: "AoC 2016 Day 21: Scrambler"
date: 2016-12-21
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Assemblers
series:
- Advent of Code 2016
---
### Source: [Scrambled Letters and Hash](http://adventofcode.com/2016/day/21)

> **Part 1:** [Another]({{< ref "2016-12-12-assembunny.md" >}}) [[wiki:virtual machine]](), of sorts. Start with the string `abcdefgh` and apply a sequence of the following commands to it:

> - swap position `X` with position `Y` = swap two positions
> - swap letter `X` with letter `Y` = swap to letters, no matter where they are
> - rotate (left|right) `X` steps = rotate forward or backward
> - rotate based on position of letter `X` = find `X`, rotate right based on its position; if the original position was >= 4, rotate one more[^arbitrary]
> - reverse positions `X` through `Y` = reverse a subset of the string
> - move position `X` to position `Y` = take a character at a position out of the string and put it somewhere else specific

<!--more-->

I most definitely over engineered this. I created a decorator that would take an instruction and register a function based on a regex...

```python
def register(regex):
    '''Register a function as a command in this simple virtual machine we are building.'''

    def outer(f):
        @functools.wraps(f)
        def inner(value, *args, **kwargs):
            new_value = f(value, *args, **kwargs)
            return new_value or value

        functions.append((re.compile(regex), inner))

        return inner
    return outer

def apply(value, command):
    '''Apply a command to the given value (look for a matching regex).'''

    def guess_type(obj):
        try:
            return int(obj)
        except:
            return obj

    for regex, function in functions:
        logging.info('- Testing {}'.format(regex))
        m = regex.match(command)
        if m:
            args = [guess_type(arg) for arg in m.groups()]
            kwargs = {k: guess_type(arg) for k, v in m.groupdict().items()}
            return function(value, *args, **kwargs)

    raise Exception('Unknown command: {}'.format(command))
```

It does make the actual functions much cleaner though, so that's something:

```python
@register(r'swap position (\d+) with position (\d+)')
def swap_indexes(value, x, y):
    value[int(y)], value[int(x)] = value[int(x)], value[int(y)]

@register(r'swap letter (\w) with letter (\w)')
def swap_letters(value, x, y):
    return [
        {x: y, y: x}.get(c, c)
        for c in value
    ]

@register(r'rotate (left|right) (\d+)')
def rotate(value, direction, offset):
    if direction == 'left':
        return value[offset:] + value[:offset]
    else:
        return value[-offset:] + value[:-offset]

@register(r'rotate based on position of letter (\w)')
def rotate_oddly(value, c):
    '''
    rotate based on position of letter X means that the whole string should be
    rotated to the right based on the index of letter X (counting from 0) as
    determined before this instruction does any rotations. Once the index is
    determined, rotate the string to the right one time, plus a number of times
    equal to that index, plus one additional time if the index was at least 4.
    '''

    index = value.index(c)

    value = rotate(value, 'right', 1)
    value = rotate(value, 'right', index)

    if index >= 4:
        value = rotate(value, 'right', 1)

    return value

@register(r'reverse positions (\d+) through (\d+)')
def reversed_section(value, x, y):
    return value[:x] + list(reversed(value[x:y+1])) + value[y+1:]

@register(r'move position (\d+) to position (\d+)')
def move_character(value, x, y):
    c = value[x]
    value.pop(x)
    value.insert(y, c)
```

Then we just apply the commands in order:

```python
value = list(args.input)
commands = list(fileinput.input(args.files))

for command in commands:
    command = command.strip()
    value = apply(value, command)

print(''.join(value))
```

> **Part 2:** Given the same series of commands, what input would produce the output `fbgdceah`?

Now this is interesting. One option would be just to try every ordering. There are only {{< inline-latex "8! = 40,320" >}} of them. But where's the fun in that? Instead, let's calculate the inverse of each function and apply them in the reverse order. :smile:

Some are easy. They're their own inverses:

```python
@register(r'invert swap position (\d+) with position (\d+)')
@register(r'swap position (\d+) with position (\d+)')
def swap_indexes(value, x, y):
    value[int(y)], value[int(x)] = value[int(x)], value[int(y)]
```

I'm adding `invert` to the beginning of each command so that I know which command I'm running:

```python
def apply_inverse(value, command):
    '''Apply the inverse of a command for a given value.'''

    return apply(value, 'invert ' + command)
```

Some are slightly more complicated and require a bit of help:

```python
@register(r'invert rotate (left|right) (\d+)')
def rotate_inverse(value, direction, offset):
    return rotate(value, 'right' if direction == 'left' else 'left', offset)

@register(r'invert move position (\d+) to position (\d+)')
def invert_move_character(value, x, y):
    move_character(value, y, x)
```

The one really interesting is that weird rotate based on position of letter... I started to work out what all the cases where (it's complicated, since it depends on what the original index of the letter was before swapping). But then I realized that there are only 8 possible values we could rotate by. Try them all:

```python
@register(r'invert rotate based on position of letter (\w)')
def rotate_oddly_but_in_reverse(value, c):
    # This is a hack, but that's a screwy function to invert...

    for offset in range(len(value)):
        test_value = rotate(value, 'left', offset)
        if rotate_oddly(test_value, c) == value:
            return test_value
```

:smile:

Now we can broaden our original code to try inverted functions if requested:

```python
value = list(args.input)

commands = list(fileinput.input(args.files))
if args.invert:
    commands = reversed(commands)

for command in commands:
    command = command.strip()
    if args.invert:
        value = apply_inverse(value, command)
    else:
        value = apply(value, command)

print(''.join(value))
```

Fun times.

[^arbitrary]: Missing this arbitrary little detail cost me more time than I care to admit...
