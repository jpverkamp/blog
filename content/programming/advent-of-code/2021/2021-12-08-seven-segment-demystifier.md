---
title: "AoC 2021 Day 8: Seven Segment Demystifier"
date: 2021-12-08 00:00:10
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
programming/topics:
- Algorithms
- Seven Segment Displays
---
### Source: [Seven Segment Search](https://adventofcode.com/2021/day/8)

#### **Part 1:** Simulate a {{< wikipedia "seven segment displey" >}} where you do not know which input wire controls which segment. Given the wires used in all ten digits and four output digits, count how many times 1, 4, 7, and 8 are outputted. 

<!--more-->

This one took me *far* longer to work out than I'd care to admit. And it wasn't at all because I had the wrong approach (I went for brute force again), but rather because I had *mistyped one character* in my input. Bah humbug. That's why you write tests... Oy.

Like I mentioned, I'm just going to try to brute force this problem. It will be slower than using their advice (the advice being that there is always 1 input with two segments (one) and 1 with 3 (seven). Instead, brute forcing all ten digits makes for much cleaner code. First, let's set up some constants:

```python
# Seven segment display
#   0:      1:      2:      3:      4:
#  aaaa    ....    aaaa    aaaa    ....
# b    c  .    c  .    c  .    c  b    c
# b    c  .    c  .    c  .    c  b    c
#  ....    ....    dddd    dddd    dddd
# e    f  .    f  e    .  .    f  .    f
# e    f  .    f  e    .  .    f  .    f
#  gggg    ....    gggg    gggg    ....
#
#   5:      6:      7:      8:      9:
#  aaaa    aaaa    aaaa    aaaa    aaaa
# b    .  b    .  .    c  b    c  b    c
# b    .  b    .  .    c  b    c  b    c
#  dddd    dddd    ....    dddd    dddd
# .    f  e    f  .    f  e    f  .    f
# .    f  e    f  .    f  e    f  .    f
#  gggg    gggg    ....    gggg    gggg

SEGMENTS = [
    {'a', 'b', 'c', 'e', 'f', 'g'},
    {'c', 'f'},
    {'a', 'c', 'd', 'e', 'g'},
    {'a', 'c', 'd', 'f', 'g'},
    {'b', 'c', 'd', 'f'},
    {'a', 'b', 'd', 'f', 'g'},
    {'a', 'b', 'd', 'e', 'f', 'g'},
    {'a', 'c', 'f'},
    {'a', 'b', 'c', 'd', 'e', 'f', 'g'},
    {'a', 'b', 'c', 'd', 'f', 'g'},
]

ALPHABET = 'abcdefg'
MAPPINGS = [
    dict(zip(ALPHABET, ordering))
    for ordering in itertools.permutations(ALPHABET)
]
```

The `SEGMENTS` define a set of correctly labeled wires goes to each segment (in order). So `0` uses all of them but `d`, `1` uses only `c` and `f`, etc. 

`MAPPINGS` is a neat trick. Using {{< doc python "itertools.permutations" >}}, we can generate all possible arrangements of the 7 letters in `ALPHABET`. We then zip each `ordering` up with `ALPHABET`, convert to a `dict` and we have a conversion. For example:

```python
>>> MAPPINGS[286]
{'a': 'a', 'b': 'd', 'c': 'c', 'd': 'g', 'e': 'f', 'f': 'b', 'g': 'e'}
>>> MAPPINGS[286]['a']
'a'
>>> MAPPINGS[286]['g']
'e'
```

In this case, input wire `a` maps to output `a`, but `g` maps to `e`, etc. 

Okay. Fun part. For each input, we have all ten digits, with the input wires that makes those up, but we don't know which mapping matches. But we do know if a `mapping` is valid, it will have to turn each of those ten inputs into one of the possible `SEGMENTS`. So we can do this:

```python
def load(file: TextIO) -> Generator[List[int], None, None]:
    '''
    Load an input file with a scrambled set of 7 segment displays than 4 output digits.'''

    for line in file:
        raw_inputs, raw_outputs = line.split(' | ')
        inputs = [set(input) for input in raw_inputs.split()]
        outputs = [set(output) for output in raw_outputs.split()]

        for mapping in MAPPINGS:
            if any(
                {mapping[v] for v in input} not in SEGMENTS
                for input in inputs
            ):
                continue

            yield [
                SEGMENTS.index({mapping[v] for v in output})
                for output in outputs
            ]
```

We'll take the input (which looks like `acedgfb cdfbe gcdfa fbcad dab cefabd cdfgeb eafb cagedb ab | cdfeb fcadb cdfeb cdbaf`), split the input and output, and then go through each `mapping`. The line `{mapping[v] for v in input}` creates the output given the mapping, so we apply that to every `input` in `inputs` and check for any *not* in `SEGMENTS`. If that's the case, the mapping isn't valid, so skip it. We should have exactly 1 mapping that's valid, so decode the outputs (using that same mapping) and `yield` the resulting digits. 

I expect that's overkill / already implementing part 2... but that's okay!

Since we have the digits, count up the 1, 4, 7, and 8 (they're the easiest to determine). 

```python
def part1(file: typer.FileText):
    print(sum(
        1 if digit in (1, 4, 7, 8) else 0
        for digits in load(file)
        for digit in digits
    ))
```

Yeah... that's it!

```bash
$ python3 seven-segment-demystifier.py part1 input.txt
349
```

#### **Part 2:** Calculate the sum of all of the 4 digit output numbers. 

Yeah... in brute forcing the entire problem rather than just solving the 'easy' 4 digits, this is already done:

```python
def part2(file: typer.FileText):
    print(sum(
        int(''.join(str(digit) for digit in digits))
        for digits in load(file)
    ))
```

So easy!

```bash
$ python3 seven-segment-demystifier.py part2 input.txt
1070957
```

#### Testing

So. The error I originally had was that I was missing one segment for the `zero`. That meant that there was never a mapping that worked. In order to debug that, I ended up writing this:

```python
if any(
    any(
        mapping[letter] not in dst
        for letter in src
    )
    for src, dst in [('ab', 'cf'), ('dab', 'acf'), ('eafb', 'bcdf')]
):
    continue

print(mapping)
failed = 0
for input in inputs:
    mapped_input = {mapping[v] for v in input}
    if mapped_input not in SEGMENTS:
        print('failed', input, '->', mapped_input)
        failed += 1

print('failed', failed)
print()
```

That way, I'm basically solving the faster mode (see below) for the single example given above (with one being `ab -> cv`, seven being `dab -> acf`, and the rest as such). That way when I printed it out... I found the single number failing. Oy vey. Anyways!

#### Timing

So... this is where it's starting to get a bit slower:

```bash
--- Day 8: Seven Segment Search ---

$ python3 seven-segment-demystifier.py part1 input.txt
349
# time 753413083ns / 0.75s

$ python3 seven-segment-demystifier.py part2 input.txt
1070957
# time 845831292ns / 0.85s
```

Still under a second... so fast enough. But I wonder if that could be optimized a bit by using the tricks they mentioned. 

For example, if you have the input:

`acedgfb cdfbe gcdfa fbcad dab cefabd cdfgeb eafb cagedb ab`

- You know that `ab` is a one (it's the only one with two segments) and maps to `cf`. 
- Likewise, you know `dab` is seven and maps to `acf`.
- Between the two, that means that the top segment has to be the input: `d`, output: `a` (it's the only one not in both). 

So one part of the mapping (`d -> a`) is set and another two `a/b -> c/f` has only two remaining options. That reduces the number of possible permutations from {{< inline-latex "P(7, 7) = 5040" >}} to {{< inline-latex "P(2, 2) * P(4, 4) = 48" >}}! That's amazing and probably worth it. 

Okay, let's write a more complicated (but faster) load function:

```python
def load2(file: TextIO) -> Generator[List[int], None, None]:
    '''
    Load an input file with a scrambled set of 7 segment displays than 4 output digits.

    Use the fact that there's only 1 possibility for one, 1 (overlapping) for seven to limit the number of permutations from 5040 to 48. 
    '''

    for line in file:
        raw_inputs, raw_outputs = line.split(' | ')
        inputs = [set(input) for input in raw_inputs.split()]
        outputs = [set(output) for output in raw_outputs.split()]

        for input in inputs:
            if len(input) == 2:
                one = input
            elif len(input) == 3:
                seven = input

        # The output that is in seven but not one maps to a
        # I wish there were a better way to get the only value out of a set
        mapping = {
            list(seven.difference(one))[0]: 'a'
        }

        # The other two values in one have to map to c and f
        for one_permutation in itertools.permutations(one):
            mapping.update(dict(zip(one_permutation, 'cf')))

            # And all the values not in seven permute the last output
            for rest_permutation in itertools.permutations(set('abcdefg') - seven):
                mapping.update(dict(zip(rest_permutation, 'bedg')))

                if any(
                    {mapping[v] for v in input} not in SEGMENTS
                    for input in inputs
                ):
                    continue

                yield [
                    SEGMENTS.index({mapping[v] for v in output})
                    for output in outputs
                ]
```

So we're going to still iterate through the mappings, but generate them in three parts. The value that's in seven but not one (the initial `mapping`), the `one_permutation` of values only in one and the `rest_permutation` of the 4 values not in seven. 

One bit of weirdness is that I'm always using the mutation'y `dict.update` function. That modifies the dictionary, which you think would mess things up... but turns out it can't. We are always using permutations of the same two/four values, so always overwriting in each iteration. Good times!

In order to hook this up, I used a [typer callback](https://typer.tiangolo.com/tutorial/commands/callback/):

```python
@app.callback()
def useLoad2(fast: bool = False):
    global load, load2

    if fast:
        load = load2
```

That's actually surprisingly simple... Does it work?

``bash
--- Day 8: Seven Segment Search ---

$ python3 seven-segment-demystifier.py part1 input.txt
349
# time 737720459ns / 0.74s

$ python3 seven-segment-demystifier.py part2 input.txt
1070957
# time 728406083ns / 0.73s

$ python3 seven-segment-demystifier.py --fast part1 input.txt
349
# time 49562583ns / 0.05s

$ python3 seven-segment-demystifier.py --fast part2 input.txt
1070957
# time 49386709ns / 0.05s
```

Heck yes it does. That's an order of magnitude speedup! And I would argue the code is not *that* much worse (although it *is* worse). Cool times. 