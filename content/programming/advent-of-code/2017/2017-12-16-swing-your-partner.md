---
title: "AoC 2017 Day 16: Swing Your Partner"
date: 2017-12-16
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Assemblers
- Virtual Machines
- Optimization
series:
- Advent of Code 2017
---
### Source: [Permutation Promenade](http://adventofcode.com/2017/day/16)

> **Part 1:** Running on the string `a...p` apply a series of the following commands:

> - `sX` rotates the string right by `X` positions
> - `xX/Y` swaps positions `X` and `Y`
> - `pA/B` swaps the letters `A` and `B` no matter their positions

<!--more-->

Let's just write that out directly:

```python
lib.add_argument('--programs', default = 'abcdefghijklmnop')
data = list(lib.param('programs'))

for line in lib.input():
    for command in line.split(','):
        # Spin, written sX, makes X programs move from the end to the front, but maintain their order otherwise.
        if command.startswith('s'):
            distance = int(command[1:])
            data = data[len(data)-distance:] + data[:len(data)-distance]

        # Exchange, written xA/B, makes the programs at positions A and B swap places.
        elif command.startswith('x'):
            x, y = map(int, command[1:].split('/'))
            data[x], data[y] = data[y], data[x]

        # Partner, written pA/B, makes the programs named A and B swap places.
        elif command.startswith('p'):
            a, b = command[1:].split('/')
            x = data.index(a)
            y = data.index(b)
            data[x], data[y] = data[y], data[x]

output = ''.join(data)
print(output)
```

Pretty straight forward and quick enough for the given input.

> **Part 2:** Repeat the same program one billion times.

{{< giphy vhkDolh4DV4RO >}}

So. First option would be to just try to write a loop around the whole thing.[^tqdm]

```bash
$ python3 swing-your-partner.py input.txt --repeat 1000000000

  0%|▏    | 1430653/999999999 [00:09<1:54:03, 145908.38it/s]
```

Yeah. I don't think I'm going to wait 2 hours for this to finish... Even running at over 150,000 iterations per second, 1 billion is just a really big number.

My second attempt was to realize that there are really two kinds of swaps going on here: `position_swaps` are a map from the original position in the string to a final position. Both `sX` and `xX/Y` do this and these never care which characters are being moved, only where they are. `character_swaps` (just `pX/Y`) swap two characters. This only cares which characters they are, not where. So they can be calculated and applied separately.

```python
# Pre-calculate a list of positions and letters that need swapped
position_swaps = list(range(len(data)))
character_swaps = []

for line in lib.input():
    for command in line.split(','):
        # Spin, written sX, makes X programs move from the end to the front, but maintain their order otherwise.
        if command.startswith('s'):
            distance = int(command[1:])
            position_swaps = position_swaps[len(data)-distance:] + position_swaps[:len(data)-distance]

        # Exchange, written xA/B, makes the programs at positions A and B swap places.
        elif command.startswith('x'):
            x, y = map(int, command[1:].split('/'))
            position_swaps[x], position_swaps[y] = position_swaps[y], position_swaps[x]

        # Partner, written pA/B, makes the programs named A and B swap places.
        elif command.startswith('p'):
            character_swaps.append((a, b))

# Parse through all swaps (in order) to figure out what each character ends up as
character_swap_map = {}
for c in data:
    out = c
    for a, b in character_swaps:
        if out == a:
            out = b
        elif out == b:
            out = a
    if c != out:
        character_swap_map[c] = out
```

We could then somehow multiply these maps one billion times and apply them directly. It works, but unfortunately, we're still doing roughly the same amount of work. But we might just have something here.

My next attempt was to combine this with {{< wikipedia "recursion" >}} and {{< wikipedia "dynamic programming" >}}. Rather than calculating the maps once and repeating them a billion times, we're going to start with a billion and split it in half. Calculate what the maps would be for 500 million and then combine the maps from the two halves. Except we don't want to do 500 million either, so split that in half. Keep going all the way down. And as a bonus, {{< wikipedia "memoize" >}} each of these halves, so we only have to calculate the two maps for a given number of repeats once.

So how in the world do we do this?

```python
@functools.lru_cache(None)
def generate_swaps(iterations):
    '''
    Recursively determine how a list will be mutated for a given number of mutations.
    '''

    # Base case: Don't change for 0 iterations
    if iterations == 0:
        return list(range(len(lib.param('programs')))), {}

    # Base case, manually calculate a single iteration
    elif iterations == 1:
        position_swaps = list(range(len(lib.param('programs'))))
        character_swaps = []

        for command in commands:
            if command.startswith('s'):
                distance = int(command[1:])
                position_swaps = position_swaps[len(position_swaps)-distance:] + position_swaps[:len(position_swaps)-distance]

            elif command.startswith('x'):
                x, y = map(int, command[1:].split('/'))
                position_swaps[x], position_swaps[y] = position_swaps[y], position_swaps[x]

            elif command.startswith('p'):
                a, b = command[1:].split('/')
                character_swaps.append((a, b))

        character_swap_map = {}
        for c in data:
            out = c
            for a, b in character_swaps:
                if out == a:
                    out = b
                elif out == b:
                    out = a
            if c != out:
                character_swap_map[c] = out

        return position_swaps, character_swap_map

    # Recursive case, split in half and combine
    else:
        i = math.floor(iterations / 2)
        j = math.ceil(iterations / 2)

        position_swaps_i, character_swap_map_i = generate_swaps(i)
        position_swaps_j, character_swap_map_j = generate_swaps(j)

        position_swaps = [
            position_swaps_i[index]
            for index in position_swaps_j
        ]

        character_swap_map = {}
        for k in set(character_swap_map_i.keys()) | set(character_swap_map_j.keys()):
            v1 = character_swap_map_i.get(k, k)
            v2 = character_swap_map_j.get(v1, v1)
            if k != v2:
                character_swap_map[k] = v2

        return position_swaps, character_swap_map
```

The base cases aren't bad. `0` just means we keep the original order and don't swap any characters. `1` is the same code that we were going to repeat a billion times above. The interesting code comes in the last case. First, we generate two halves recursively. Then we have to merge the two maps.

For `position_swaps`, we can actually just apply one map to the other one. This works because the position swaps are {{< wikipedia transitive >}}.

For `character_swaps`, it's a bit more complicated. We have four cases:

- `a` became `b` in the first half, but `b` doesn't change in the second half: add `a` -> `b` to the final map
- `a` became `b` in the first half and `b` became `c` in the second half: add `a` -> `c` to the final map
- `a` doesn't change in the first half, but `a` becomes `b` in the second half: add `a` -> `b` to the final map
- `a` becomes `b` in the first half, but `b` becomes `a` in the second half (this is actually pretty common since we're exchanging characters); don't add anything to the final map

In the last case, we could have added `a` -> `a` to the final map, but as an optimization I removed it instead. As mentioned, this is actually a common case, so removing these likely has a decent speed boost (I didn't actually try it without, so that could be wrong).

So we have a set of `position_swaps` and `character_swaps` for one billion iterations (or whatever number we want). How do we apply them?

```python
position_swaps, character_swap_map = generate_swaps(lib.param('repeat'))
data = [
    character_swap_map.get(data[index], data[index])
    for index in position_swaps
]

output = ''.join(data)
print(output)
```

Seems like that should be more complicated than it is.

The crazy thing? It's **wicked** fast:

```bash
day-16  python3 swing-your-partner.py input.txt 0.1947190761566162      kpfonjglcibaedhm
day-16  python3 dynamic-swing.py input.txt      0.08614611625671387     kpfonjglcibaedhm
day-16  python3 dynamic-swing.py input.txt --repeat 1000000000  0.0846567153930664      odiabmplhfgjcekn
```

It actually runs just as quickly for a single iteration as it does for one billion. And in either case, it's doing it twice as quickly as the original solution was for just one iteration. Given that the estimate was two hours... I think this is a worthwhile case of optimization. :smile:

[^tqdm]: Using [tqdm](https://github.com/noamraph/tqdm) for an easy progress bar and estimated time to finish. That is a most excellent library.
