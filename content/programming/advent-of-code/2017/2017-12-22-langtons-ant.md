---
title: "AoC 2017 Day 22: Langton's Ant"
date: 2017-12-22
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2017
---
### Source: [Sporifica Virus](http://adventofcode.com/2017/day/22)

> **Part 1:** Implement a {{< wikipedia "cellular automaton" >}} on an infinite grid of `.` and `#` pixels such that:

> 1. Start at `(0, 0)`, facing `Up`
> 2. Repeat:
>   - If the cursor is on `.` swap it to `#` and turn `Left`
>   - If the cursor is on `#` swap it to `.` and turn `Right`
>   - Either way, after turning, move forward once

> After 10,000 iterations, how many pixels were turned from `.` to `#`?

<!--more-->

As you might guess from the title of this post, this is {{< wikipedia "Langton's Ant" >}}.

The problem statement is a bit short since I've already solved this problem [back in 2014]({{< ref "2014-08-07-langtons-ant.md" >}}) with a whole pile of cool animations. Head back that way if you want to see another take on this problem in Racket.

First, we want to decide on a representation and load in the initial data. Since the grid that we're working on can (and will) grow indefinitely, we want something that doesn't have to resize to do it. For this, I'm going to use a `set` of coordinates that contains all of the `infected` pixels (`#`). We can assume that any point that isn't in this set is `.`.

```python
# Load the initial state, assuming a square; recenter on the center of the data
# . is assumed to be the default state and not stored
data = ''.join(lib.input(include_comments = True))

size = int(math.sqrt(len(data)))
offset = -(size // 2)

infected = {}

for x in range(size):
    for y in range(size):
        if data[y * size + x] == '#':
            infected.add((x, y))
```

The code is a bit odd here, since the initial load will start with `(0, 0)` in the top left, but I want it to be in the center of the input. That's not really necessary, since the simulation doesn't care about coordinates, but it will be more consistent.

Also, we're using the `include_comments` parameter on `lib.input`, which I haven't used before. This is because we're expecting Python style comments, which start with `#`. So if a line in the input grid starts with `#`, that line will be ignored, which isn't what we want. That took a bit to figure out. :smile:

Next, we run the actual simulation:

```python
# Run the simulation
location = (0, 0)
facing = (0, -1)

caused_infection = 0

for tick in range(0, lib.param('iterations')):
    infected ^= {location}
    if location not in infected:
        caused_infection += 1

    facing = lib.vector2_rotate(facing, 1 if location in infected else 3)
    location = lib.vector_add(location, facing)

print(f'{caused_infection} new infections')
```

`lib.vector2_rotate` is designed for 90° turns:

```python
def vector2_rotate(v, turns_clockwise = True):
    (x, y) = v
    for i in range(turns_clockwise):
        (x, y) = (-y, x)
    return (x, y)
```

Because we have a set, `infected ^= {location}` says remove the point from `infected` if it was in it and add it if not (it's an {{< wikipedia xor >}}). This works since `.` always becomes `#` and vice versa. Finally we update the direction we are `facing` and our `location` and continue. It's nicely elegant.

> **Part 2:** Expand to four state transitions:

> - If `clean`, become `weakened` and turn `left`
> - If `weakened`, become `infected` and do not turn
> - If `infected`, become `flagged` and turn `right`
> - If `flagged`, become `clean` and `reverses` (turns `left` twice)

> Run the simulation for 10000000 ticks.

The `infected` `set` worked well enough when we only had two states, but now that we have four, we really want a `dict` instead:

```python
state = {}

for x in range(size):
    for y in range(size):
        if data[y * size + x] != '.':
            state[x + offset, y + offset] = data[y * size + x]
```

We could go ahead and hard code the transitions the same time as we did last time, but instead we should go ahead and make our code flexible enough to handle any possible combinations of transitions[^engineering]. Specifically, I will allow the user to specify transitions on the command line as such:

```python
# Load the transition table
# Map of input -> (output, # turns clockwise)
predefined_transitions = {
    'default': '#>. .>>>#',
    'evolved': '.>>>W W# #>F F>>.',
}
mode = lib.param('mode')
mode = predefined_transitions.get(mode, mode)
```

Rules are space separated. Each rule has the input character first, the output character last, and a number of `>` equal to how many times you would turn right. So the rules from above become[^default]:

| Input      | Output     | Turn      | Code    |
|------------|------------|-----------|---------|
| `clean`    | `weakened` | `left`    | `.>>>W` |
| `weakened` | `infected` |           | `W#`    |
| `infected` | `flagged`  | `right`   | `#>F`   |
| `flagged`  | `clean`    | `reverse` | `F>>.`  |


Next, we have to update the simulation to handle the new transitions:

```python
caused_infection = 0

for tick in range(0, lib.param('iterations')):
    current = state.get(location, '.')
    output, turns = transitions.get(current, (current, 0))

    if output == '.':
        del state[location]
    else:
        state[location] = output

    facing = lib.vector2_rotate(facing, turns)
    location = lib.vector_add(location, facing)

    if output == '#':
        caused_infection += 1

print(f'{caused_infection} new infections')
```

It's really not that much worse. The `if output == '.'` line is used since we assume the default state is `.`, so we don't use as much memory storing any locations that were non-`clean` and became `clean` later.

I could easily generate images from this using the same `generate_image` I've used a few times recently, but I made a pile of them already for my last post [on Langton's Ants]({{< ref "2014-08-07-langtons-ant.md" >}}). Go look at those. :smile:

```bash
$ python3 run-all.py day-22

day-22  python3 langtons-ant.py input.txt --iterations 10000    0.1982278823852539      5266 new infections
day-22  python3 langtons-ant.py input.txt --iterations 10000000 --mode evolved  88.76584982872009       2511895 new infections
```

Another case that's slightly longer than the minute I'd like, but it's close enough for now. If I hard coded the transitions, for example, it would likely run a decent bit more quickly.

[^engineering]: Over engineering? Who's over engineering? :innocent:
[^default]: Look familiar? That's the `evolved` preset. So `--mode evolved` is equivalent to `--mode ".>>>W W# #>F F>>."`
