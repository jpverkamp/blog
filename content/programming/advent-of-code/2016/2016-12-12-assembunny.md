---
title: "AoC 2016 Day 12: Assembunny"
date: 2016-12-12
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Assemblers
- Virtual Machines
series:
- Advent of Code 2016
---
### Source: [Leonardo's Monorail](http://adventofcode.com/2016/day/12)

> **Part 1:** Create a {{< wikipedia "virtual machine" >}} that has four registers (`a`, `b`, `c`, and `d`) and can process the following instructions:

> - `cpy x y` - copies `x` into `y` (`x` can be an integer or a register)
> - `inc x` - increases register `x` by one
> - `dec x` - decreases register `x` by one
> - `jnz x y` - jumps over `y` instructions if `x` is not zero (`x` can be an integer or a register)

> What is the final value in register `a`?

<!--more-->

Let's make a {{< wikipedia "virtual machine" >}}!

```python
class APC(object):
    def __init__(self, code):
        self._code = code
        self._pc = 0
        self._registers = {k: 0 for k in 'abcd'}

    def __repr__(self):
        return 'APC<{}, {}, {}>'.format(
            id(self),
            self._pc,
            self._registers,
        )

    def run(self):
        def val(x):
            try:
                return int(x)
            except:
                return self._registers[x]

        try:
            while True:
                cmd, *args = self._code[self._pc]
                logging.info('{} running {}({})'.format(self, cmd, args))

                if cmd == 'cpy':
                    self._registers[args[1]] = val(args[0])

                elif cmd == 'inc':
                    self._registers[args[0]] += 1

                elif cmd == 'dec':
                    self._registers[args[0]] -= 1

                elif cmd == 'jnz':
                    if val(args[0]) != 0:
                        self._pc += val(args[1]) - 1

                self._pc += 1

        except Exception as ex:
            logging.info('Exception: {}'.format(ex))
            self.exception = ex
```

In true {{< doc python EAFP >}} style, I'm using the out of bounds exception to halt execution. Other than that, the translations are pretty direct.

```python
instructions = [
    line.strip().split()
    for line in fileinput.input(args.files)
    if line.strip()
]

apc = APC(instructions)

print('Initial:', apc)
apc.run()
print('Final:', apc)
```

> **Part 2:** If register `c` starts with the value `1`, what is the final value left in `a`?

Let's modify the `__init__` function to take in initial values for any registers and then read those in with {{< doc python argparse >}}:

```python
class APC(object):
    def __init__(self, code, registers):
        self._code = code
        self._pc = 0
        self._registers = {k: registers.get(k, 0) for k in 'abcd'}
    ...

registers = {
    arg.split('=')[0].strip(): int(arg.split('=')[1].strip())
    for arg in args.registers
}

apc = APC(instructions, registers)
```

Nice when part 1 is flexible enough to solve part 2 with minimal changes.
