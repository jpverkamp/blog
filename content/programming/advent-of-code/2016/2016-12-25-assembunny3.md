---
title: "AoC 2016 Day 25: Assembunny3"
date: 2016-12-25
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
### Source: [Clock Signal](http://adventofcode.com/2016/day/25)

> **Part 1:** Take the [assembunny interpreter from day 12]({{< ref "2016-12-12-assembunny.md" >}}) and add one new instruction (out `x`) which transmits the value `x` (either an integer or register). Find the lowest value we can initialize `a` to so that the `out`put signals form an infinite repeating pattern of `0`, `1`, `0`, `1`, ...

<!--more-->

As before, we're going to take the `APC` class [from day 12]({{< ref "2016-12-12-assembunny.md" >}}) and add to it. This time, we need two things:

- The `out` command, along with a way to track output
- The ability to detect when we're in a loop

Since the command space is completely deterministic and there are no self-modifying instructions, it's actually fairly easy to determine if we've got a loop (in most cases). If we ever get to exactly the same state (the values of all four registers plus the current program counter), the output will loop from that point on. The only counter examples would be if any of the registers grows in an unbounded manner, but let's start by assuming that won't happen.

Here's the new `APC` class:

```python
class APC(object):
    def __init__(self, code, registers):
        self._code = code
        self._pc = 0
        self._registers = {k: registers.get(k, 0) for k in 'abcd'}
        self._output = []

    def __repr__(self):
        return 'APC<{}, {}, {}, {}>'.format(
            id(self),
            self._pc,
            self._registers,
            self._output,
        )

    def output(self):
        '''Return output as a string.'''

        return ''.join(str(el) for el in self._output)

    def run(self):
        def val(x):
            try:
                return int(x)
            except:
                return self._registers[x]

        seen_states = set()

        while True:
            if not (0 <= self._pc < len(self._code)):
                break

            # Automatically halt if we see a state we've seen before
            state = (self._pc, tuple(v for k, v in sorted(self._registers.items())))
            if state in seen_states:
                break
            else:
                seen_states.add(state)

            cmd, *args = self._code[self._pc]

            if cmd == 'cpy':
                self._registers[args[1]] = val(args[0])

            elif cmd == 'inc':
                self._registers[args[0]] += 1

            elif cmd == 'dec':
                self._registers[args[0]] -= 1

            elif cmd == 'jnz':
                if val(args[0]) != 0:
                    self._pc += val(args[1]) - 1

            elif cmd == 'out':
                self._output.append(val(args[0]))

            self._pc += 1
```

The interesting parts are the `self._output` field and its corresponding `output()` function along with the duplicate state detection in `run`. Using this, it will automatically stop when a loop is detected. We can use that to find the first value that will output `010101...`

```python
instructions = [
    line.strip().split()
    for line in fileinput.input(args.files)
    if line.strip()
]

for a_value in itertools.count():
    apc = APC(instructions, {'a': a_value})
    apc.run()

    output = apc.output()

    if args.show_output:
        print('{:05d} {}'.format(a_value, output))

    if apc.output() == ('01' * (len(output) // 2)):
        print('Found a repeating signal when a = {}'.format(a_value))
        break
```

If you print the output as you go, there's an interesting pattern:

```bash
$ python3 assembunny3.py input.txt --show_output

00000 010101111001
00001 110101111001
00002 001101111001
00003 101101111001
00004 011101111001
00005 111101111001
00006 000011111001
00007 100011111001
00008 010011111001
00009 110011111001
00010 001011111001
00011 101011111001
00012 011011111001
00013 111011111001
00014 000111111001
00015 100111111001
00016 010111111001
00017 110111111001
00018 001111111001
00019 101111111001
00020 011111111001
00021 111111111001
00022 000000000101
00023 100000000101
00024 010000000101
00025 110000000101
...
```

The program will always output 12 times before looping plus we are counting something. If you modify the above code to reverse the repeating part of the signal and print it out as a decimal (`int(''.join(reversed(output)), 2))`):

```bash
$ python3 assembunny3.py input.txt --show_output

00000 010101111001 2538
00001 110101111001 2539
00002 001101111001 2540
00003 101101111001 2541
00004 011101111001 2542
00005 111101111001 2543
00006 000011111001 2544
00007 100011111001 2545
00008 010011111001 2546
00009 110011111001 2547
00010 001011111001 2548
00011 101011111001 2549
00012 011011111001 2550
00013 111011111001 2551
00014 000111111001 2552
00015 100111111001 2553
00016 010111111001 2554
00017 110111111001 2555
00018 001111111001 2556
00019 101111111001 2557
00020 011111111001 2558
00021 111111111001 2559
00022 000000000101 2560
00023 100000000101 2561
00024 010000000101 2562
00025 110000000101 2563
```

The target value `010101010101` reversed it `101010101010`, which is 2730 in decimal. We started at 2538, so 2730 will appear after 192 iterations. If you run out the loop long enough:

```bash
$ python3 assembunny3.py input.txt --show_output

...
00180 011110010101 2718
00181 111110010101 2719
00182 000001010101 2720
00183 100001010101 2721
00184 010001010101 2722
00185 110001010101 2723
00186 001001010101 2724
00187 101001010101 2725
00188 011001010101 2726
00189 111001010101 2727
00190 000101010101 2728
00191 100101010101 2729
00192 010101010101 2730
Found a repeating signal when a = 192
```

Bingo.

And that's it. Only one part on Day 25.

I had a lot of fun doing these, I hope you had as much fun reading them. If you'd like to see the entire list, you can do so [here]({{< ref "2016-12-01-advent-of-code-year-2.md" >}}).
