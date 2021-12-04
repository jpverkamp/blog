---
title: "AoC 2021 Day 3: Binary Contraption"
date: 2021-12-03
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
---
### Source: [Binary Diagnostic](https://adventofcode.com/2021/day/3)

#### **Part 1:** Given a list of binary numbers, calculate gamma such that each bit is the most common bit in that position in the input and epsilon which is the binary inverse of gamma. Return the product. 

<!--more-->

I feel like this one could have been expressed a bit more elegantly, but I think the point is still clear enough:

```python
def part1(lines: typer.FileText):
    # Keep track of how many lines we counted total and just the number of ones
    counter = 0
    one_counts = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        counter += 1

        # If we don't have an initalized counts, start with '0' or '1'
        if not one_counts:
            one_counts = list(map(int, line))

        # Otherwise, add for any ones
        else:
            for i, bit in enumerate(line):
                if int(bit) == 1:
                    one_counts[i] += 1

    # Recombine into a binary number, that is the gamma rate
    # The epsilon rate is the inverse
    gamma = ''.join(
        '1' if bit > counter / 2 else '0'
        for bit in one_counts
    )
    epsilon = ''.join(
        '1' if bit == '0' else '0'
        for bit in gamma
    )

    print(f'{gamma=}={int(gamma, 2)}, {epsilon=}={int(epsilon, 2)}, product={int(gamma, 2)*int(epsilon, 2)}')
```

In this case, we're going to keep a running count of the number of ones in each position in `one_counts` (we have to initialize the first time through). Most of the loop counts that using `enumerate` to get the positions. 

Then when we're done, if the number of ones is greater than half the number of inputs, `1` was more common. Otherwise, `0`. Turn those back from binary to integers with `int(bits, 2)` and multiply and we're done. 

For my particular input:

```bash
$ python3 binary-contraption.py part1 input.txt
gamma='100100101010'=2346, epsilon='011011010101'=1749, product=4103154
```

#### **Part 2:** Given a list of binary numbers repeatedly filter the list such that in iteration `i`, only numbers with the most/least common bit in that position of numbers remaining is kept. After each set has been reduced to one number, return the product of the most/least values. 

That's a bit confusingly worded, but as an example, consider if, after 3 iterations, we have the list: 

* `00100`
* `11110`
* `10110`
* `10111`
* `10101`

We're on the 4th iteration, so the most common 4th bit is `1`. If we're evaluating 'most', keep the middle 3 values. If we're evaluating the least, keep only the first and last. 

Full code:

```python
def part2(lines: typer.FileText):
    # Load the entire file into memory this time
    lines = [
        line.strip()
        for line in lines
        if line.strip()
    ]

    potential_generators = copy.copy(lines)
    potential_scrubbers = copy.copy(lines)

    # Helper to find the most/least common bit in a given position from a given list
    # Note, the >= here is necessary to break ties (resulting in 1 for most common, 0 for least)
    def most_common(data, position):
        one_count = sum(
            1 if (line[position] == '1') else 0
            for line in data
        )
        return '1' if (one_count >= len(data) / 2) else '0'

    def least_common(data, position):
        return '1' if most_common(data, position) == '0' else '0'

    # Helper to filter an iterable so that lines with line[position] = value are kept
    def filter_position_equals(data, position, value):
        return list(filter(lambda line: line[position] == value, data))

    # Iterate through the bits
    for position in range(len(lines[0])):
        if len(potential_generators) > 1:
            potential_generators = filter_position_equals(
                potential_generators,
                position,
                most_common(potential_generators, position)
            )

        if len(potential_scrubbers) > 1:
            potential_scrubbers = filter_position_equals(
                potential_scrubbers,
                position,
                least_common(potential_scrubbers, position)
            )

    generator = int(potential_generators[0], 2)
    scrubber = int(potential_scrubbers[0], 2)

    print(
        f'{potential_generators=}={generator}, {potential_scrubbers=}={scrubber}, product={generator*scrubber}')
```

They are getting a bit longer, aren't they? Fun though!

There was a gotcha (as mentioned in the comment) on what to do if you have an even number of current values with equal number of 1s and 0s. In that case, it's spelled out in the full problem statement: on a tie, use 1 for most common and 0 for least. 

```bash
$ python3 binary-contraption.py part2 input.txt
potential_generators=['110101000111']=3399, potential_scrubbers=['010011100001']=1249, product=4245351
```

#### Timing

Timing wise, we're still in the basically instant camp:

```bash
--- Day 3: Binary Diagnostic ---

$ python3 binary-contraption.py part1 input.txt
gamma='100100101010'=2346, epsilon='011011010101'=1749, product=4103154
# time 34395958ns / 0.03s

$ python3 binary-contraption.py part2 input.txt
potential_generators=['110101000111']=3399, potential_scrubbers=['010011100001']=1249, product=4245351
# time 35739667ns / 0.04s
```