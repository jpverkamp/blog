---
title: "AoC 2016 Day 11: Radiation Avoider"
date: 2016-12-11
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Backtracking
- Data Structures
- Optimization
series:
- Advent of Code 2016
---
### Source: [Radioisotope Thermoelectric Generators](http://adventofcode.com/2016/day/11)

> **Part 1:** Input will be a list of the following form:

> - The first floor contains a hydrogen-compatible microchip and a lithium-compatible microchip.
> - The second floor contains a hydrogen generator.
> - The third floor contains a lithium generator.
> - The fourth floor contains nothing relevant.

> You have an elevator that can move exactly 1 or 2 items. You can only leave a microchip on a floor with a non-matching generator if a matching generator is also present.

> Move all items to the top (4th) floor.

<!--more-->

Plan of attack: create a simulation and the perform a [[wiki:breadth first search]]() to find the fastest solution. This might have issues depending on how large the solution space is, but we can start with this.

First, represent the microchips and generators:

```python
class Thing(object):
    def __init__(self, element): self.element = element
    def __repr__(self): return '{}<{}>'.format(self.__class__.__name__, self.element)
    def __hash__(self): return hash(repr(self))
    def __eq__(self, other): return repr(self) == repr(other)
    def __lt__(self, other): return repr(self) < repr(other)

class Generator(Thing): pass
class Microchip(Thing): pass
```

The main interesting part here is that I have implemented `__hash__`, `__eq__` and `__lt__`. This means that either `Generators` and `Microchips` can be put in a {{< doc python set >}} or they can be {{< doc python sorted >}}.

Next, a class that can represent the current 'state' of the solution. This should be the current location of all `Things` and the elevator, along with being able to generate any next states we can get to from this one:

```python
class State(object):
    def __init__(self, floors, elevator = 0, steps = None):
        self._elevator = elevator
        self._floors = floors
        self._steps = steps or []
        self._hash = hash(repr(self))

    def __repr__(self):
        '''Simple output for repr that doesn't include steps (since this is used by hash).'''

        floor_strings = []
        for items in self._floors:
            if items:
                floor_strings.append(' '.join(repr(item) for item in sorted(items)))
            else:
                floor_strings.append('∅')

        return 'State<{}, {}>'.format(self._elevator, ', '.join(floor_strings))

    def __str__(self):
        '''Nicer output for str(state) that includes steps.'''

        floors = []
        for i, floor in enumerate(self._floors):
            level_part = ('[{}]' if self._elevator == i else ' {} ').format(i + 1)
            item_part = ' '.join(str(item) for item in sorted(floor))
            floors.append(level_part + ' ' + item_part)
        return '\n'.join(reversed(floors))

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        return hash(self) == hash(other)

    def steps(self):
        '''Return the steps taken by this object.'''

        return copy.copy(self._steps)

    def move(self, delta, items):
        '''
        Return a new state resulting from moving the elevator by delta (-1/+1) and take items with it.

        If the new state isn't valid, return None.
        '''

        if not (0 <= self._elevator + delta < len(self._floors)):
            return

        new_floors = copy.deepcopy(self._floors)
        for item in items:
            new_floors[self._elevator].remove(item)
            new_floors[self._elevator + delta].add(item)

        new_state = State(
            floors = new_floors,
            elevator = self._elevator + delta,
            steps = self._steps + [(delta, items)],
        )

        if new_state.is_valid():
            return new_state

    def is_valid(self):
        '''
        A state is invalid if a microchip is on a floor with a generator, but
        does not have its own generator.
        '''

        for floor in self._floors:
            chips = {item for item in floor if isinstance(item, Microchip)}
            generators = {item for item in floor if isinstance(item, Generator)}

            # If there are no generators, the chips are safe
            if not generators:
                continue

            # At least one powered chip
            # If there are any chips that don't have a matching generator, they are not safe
            if any(chip for chip in chips if not Generator(chip.element) in generators):
                return False

        return True

    def is_solved(self):
        '''If all items are on the top floor, the puzzle is solved.'''

        return not any(self._floors[:-1])

    def next_states(self):
        '''Return all valid next states possible from moving 1-2 items up or down a floor.'''

        for delta in [-1, 1]:
            for count in [1, 2]:
                for items in itertools.combinations(self._floors[self._elevator], count):
                    new_state = self.move(delta, items)
                    if new_state:
                        yield new_state
```

There's a fair bit to unpack there, so let's go through it bit by bit.

First, some setup. The `__init__` method constructs a new state, `__str__` makes printing look nicer (mostly for debugging), and `__repr__` creates a machine readable version of the state. This is the most important part, since `__repr__` is used to construct the hash, which in turn is used to avoid recalculating duplicate states. No matter how we got to it, if the pieces are on the same floors, it's the same state.

Next, a few helper functions to check our current state. `is_solved` will return `True` if all of the items are on the top floor. `is_valid` will check the condition that an unpowered microchip cannot share a floor with a powered one. {{< doc python any >}} is nice.

Finally, we want to calculate all possible moves from the given state to the next state. The `move` function does that for a single elevator movement (returning `None` if the new state doesn't work) and `next_states` creates an iterator that will return all possible ways that we could move the elevator. {{< doc python "itertools.combinations" >}} is rather handy for this.

Now that we have the simulation layed out, we have a bit to load the initial state from a file:

```python
# Read the initial state from the given input file
re_object = re.compile(r'(\w+)(?:-compatible)? (generator|microchip)')
with open(args.input, 'r') as fin:
    floors = []
    for line in fin:
        if not line.strip() or line.startswith('#'):
            continue

        floor = set()
        for element, type in re_object.findall(line):
            if type == 'generator':
                floor.add(Generator(element))
            elif type == 'microchip':
                floor.add(Microchip(element))

        floors.append(floor)

    initial_state = State(floors)
```

And the actual [[wiki:breadth first search]]():

```python
# Use a BFS to find the fastest solution
def solve(initial_state):
    queue = [initial_state]
    duplicates = {initial_state}

    while queue:
        state = queue.pop(0)
        count += 1

        if state.is_solved():
            return state

        for next_state in state.next_states():
            if next_state in duplicates:
                duplicate_count += 1
            else:
                queue.append(next_state)
                duplicates.add(next_state)

final_state = solve(initial_state)

print('''\
=== Solution ===

Initial state:
{initial}

Final state:
{final}

Steps:
{steps}
'''.format(
    count = len(final_state.steps()),
    initial = initial_state,
    final = final_state,
    steps = '\n'.join(
        '{}: {} {}'.format(i + 1, delta, items)
        for i, (delta, items) in enumerate(final_state.steps())
    ),
))
```

I should probably abstract out the code to do a search like that. We use it all of the time.

> **Part 2:** Add the following elements to the first floor:

> - An elerium generator.
> - An elerium-compatible microchip.
> - A dilithium generator.
> - A dilithium-compatible microchip.

Mostly, this just makes the puzzle *far* longer. It is no longer really feasible to run the direct solution. With 14 items that can each be on one of 4 floors, there are {{< inline-latex "4^{14} = 268,435,456" >}} possible states (many not valid). With a fast enough simulation, that's doable, but mine isn't super fast.

Instead, we can make an intuitive leap that took me rather a long time to think of: *there's no difference between the elements*.

So long as the generator and microchip match, there's no difference between having elerium[^xcom] on floor 1 and dilithium[^startrek] on floor 2 versus having dilithium on floor 1 and elerium on floor 2.

So what we can do is modify the `__repr__` function so that those two states have the same representation. This in turn will update the `__hash__` function so that we won't visit either state if we've already seen the other.

```python
def __repr__(self):
    '''Simple output for repr that doesn't include steps (since this is used by hash).'''

    # Optimization: Parts are interchangeable, rewrite them by order
    # This will assign an index the first time it sees a name and use that any more
    # So parts will always be ordered from lowest to highest, ties broken alphabetically
    def ordered_rewrite(m, cache = {}):
        type, name = m.groups()

        if name not in cache:
            cache[name] = str(len(cache))

        return '{}{}'.format(type[0], cache[name])

    floor_strings = []
    for items in self._floors:
        if items:
            floor_strings.append(' '.join(repr(item) for item in sorted(items)))
        else:
            floor_strings.append('∅')

    return re.sub(
        r'(Microchip|Generator)<([^<>]+)>',
        ordered_rewrite,
        'State<{}, {}>'.format(self._elevator, ', '.join(floor_strings)),
    )
```

The trick here is apply a regex with a function (`ordered_rewrite`) that will rewrite each element with a number based on the order they appear in the string. This requires that Python's regex engine does replacements in the same order all the time, but that does actually work out. Using this, the solution is still relatively slow, but I did finally get an actual answer.

[^xcom]: I love [[wiki:X-COM|that game]]().
[^startrek]: A pretty [[wiki:Star Trek|good show]]() too.
