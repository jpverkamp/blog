---
title: "AoC 2016 Day 23: Assembunny2"
date: 2016-12-23
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2016
---
### Source: [Safe Cracking](http://adventofcode.com/2016/day/23)

> **Part 1:** Take the [assembunny interpreter from day 12]({{< ref "2016-12-12-assembunny.md" >}}) and add an instruction (tgl `X`) that modifies the code at an offset of `X` instructions.

> - `inc` becomes `dec`; any other one argument instruction (including `tgl`) becomes `inc`
> - `jnz` becomes `cpy`; any other two argument instructions become `jnz`
> - Toggling an instruction outside of the program does nothing (it does not halt execution)
> - If toggling produces an invalid instruction, ignore it

> Run the given program with the initial register of `a = 7`. What is the final value in register `a`?

<!--more-->

For the most part, take the `APC` object from [day 12]({{< ref "2016-12-12-assembunny.md" >}}) and add the new instruction:

```python
class APC(object):
    ...

    def run(self):
        ...
        elif cmd == 'tgl':
            target = self._pc + val(args[0])
            if 0 <= target < len(self._code):
                old_cmd, *old_args = self._code[target]

                if len(old_args) == 1:
                    new_cmd = 'dec' if old_cmd == 'inc' else 'inc'
                elif len(old_args) == 2:
                    new_cmd = 'cpy' if old_cmd == 'jnz' else 'jnz'

                self._code[target] = [new_cmd] + old_args
        ...
```

Other than that, our code already ignores invalid instructions inline, so just run the new program in the same way as [before]({{< ref "2016-12-12-assembunny.md" >}}).

> **Part 2:** Run the same program with `a = 12`.

This should be a simple matter of just changing the parameters, but that doesn't actually work. The problem is that the code is just too inefficient. With the given commands, some instructions are incredibly inefficient. For example, adding `a` plus `b` requires at least `3b` instructions (increment `a`, decrement `b`, and jump back to do it again until `b` is zero). If we want to multiply (per the hint)[^bunnies], that takes just as many repeated additions... If the numbers are large...

What we need are a few additional instructions and the ability to optimize our program.

Specifically, we want the ability to `add` and `mul`tiply:

```python
class APC(object):
    ...

    def run(self):
        ...
        # Used by optimizations
        elif cmd == 'nop':
            pass

        elif cmd == 'add':
            self._registers[args[2]] = val(args[0]) + val(args[1])

        elif cmd == 'mul':
            self._registers[args[2]] = val(args[0]) * val(args[1])
        ...
```

To get to those though, we need to recognize a few common patterns:

```text
# This is addition: add X Y X
inc X
dec Y
jnz Y -2

# This is also addition: add X Y Y
dec X
inc Y
jnz X -2
```

In each case, we don't want to change the number of instructions (since jumps are relative, that would change jump offsets), so we change each of those to an `add`, a `copy` (to zero the other register, which looping addition would do), and a `nop` which does nothing but take up space.

```python
class APC(object):
    ...

    def optimize(self):
        '''Apply a few hand rolled optimizations to the code.'''

        code = '\n'.join(' '.join(line) for line in self._code)

        replacements = [
            (   # Addition (v1)
                r'inc ([a-d])\ndec ([a-d])\njnz \2 -2',
                r'add \1 \2 \1\ncopy 0 \2\nnop',
            ),
            (   # Addition (v2)
                r'dec ([a-d])\ninc ([a-d])\njnz \1 -2',
                r'add \1 \2 \2\ncopy 0 \1\nnop',
            ),
        ]

        for pattern, replacement in replacements:
            code = re.sub(pattern, replacement, code)

        self._code = [line.split() for line in code.split('\n')]
```

It's ugly, but it works. The code is already much quicker. But in addition to addition [^heh], we can recognize multiplication:

```text
# This is multiplication: mul Y Z X
inc X
dec Y
jnz Y -2
dec Z
jnz Z -5
```

Apply this before the additions above (since the first half of that is addition already) or change the pattern so that it uses addition and you have something much faster.

Now we can run `a = 12` in a matter of seconds.

It's a bit ugly to use regular expressions for this, but for just what we're solving, it works well enough. One of these days, I want to try to write a 'real' optimizing compiler for something. I'm just the special sort of crazy that is fascinated by things like that. 

[^bunnies]: Because bunnies are known for having lots of children. Get it?[^jokes]
[^jokes]: It's funny when you explain the joke.[^jokes2][^jokes3]
[^jokes2]: No it's not.
[^jokes3]: Sometimes it is!
[^heh]: Heh.
