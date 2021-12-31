---
title: "AoC 2021 Day 18: Pairs of Pairs"
date: 2021-12-18 00:00:05
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
programming/topics:
- Data Structures
---
### Source: [Snailfish](https://adventofcode.com/2021/day/18)

#### **Part 1:** Given the following definition of Snailfish numbers, add a series of Snailfish numbers and return the magnitude of the result.

<!--more-->

* A `Snailfish` number is defined as a pair {{< inline-latex "\langle a, b \rangle" >}} where `a` and `b` can either by integers or nested `Snailfish` number
* To add two `Snailfish` numbers, {{< inline-latex "c + d = \langle c, d \rangle" >}}
* To reduce a `Snailfish` number to simplest form:
    * If there are any pairs (of integers {{< inline-latex "\langle e, f \rangle" >}}) nested 5+ levels deep, `explode` the leftmost one
        * `e` is added to the *rightmost* node *left* of the exploded pair (if possible)
        * `f` is added to the *leftmost* node *right* of the exploded pair (if possible)
        * Replace the original pair with a `0` (I missed this for a while...)
    * If there are no such pairs and there is at least one integer `g` greater than or equal to 10, `split` it into a pair {{< inline-latex "\langle h, i \rangle" >}} such that {{< inline-latex "h = \left \lfloor \frac{g}{2} \right \rfloor, i = \left \lceil \frac{g}{2} \right \rceil" >}}. 
* The magnitude of {{< inline-latex "|\langle j, k \rangle| = 3|j|+2|k|" >}} 

Yeah... that took a bit to figure out. 

To just parse the numbers, do addition, and do `split`, the most natural data structure is going to be a tree:

```python
@dataclass(frozen=True)
class Snailfish():
    left: Union[int, 'Snailfish']
    right: Union[int, 'Snailfish']

    @staticmethod
    def read(text: TextIO) -> Optional[Union[int, 'Snailfish']]:
        '''Read a snailfish from the given filelike object'''

        c = text.read(1)
        while not c.isdigit() and not c in '[':
            c = text.read(1)

        if c == '[':
            left = Snailfish.read(text)
            right = Snailfish.read(text)

            assert left is not None
            assert right is not None

            return Snailfish(left, right)

        elif c.isdigit():
            the_once_and_future_number = []

            while c.isdigit():
                the_once_and_future_number.append(c)
                c = text.read(1)

            assert(c == ',' or c == ']')

            return int(''.join(the_once_and_future_number))

        return None

    def reduce(self) -> 'Snailfish':
        '''Convert this snailfish to minimum form using the result for explosing and splitting.'''

        # TODO

    def magnitude(self) -> int:
        '''Calculate the magnitude of a snailfish number.'''

        def f(sf: Union[int, 'Snailfish']) -> int:
            if isinstance(sf, int):
                return sf
            else:
                return 3 * f(sf.left) + 2 * f(sf.right)

        return f(self)

    def __add__(self, other):
        '''Add two Snailfish by making a larger pair and then reducing it.'''

        return Snailfish(self, other).reduce()

    def __repr__(self):
        return f'{{{self.left}, {self.right}}}'
```

But... it's really quite tricky to use a tree and deal with exploding. You can probably recur up the tree and back down to find the *rightmost left node*... but why? Instead, we're going to swap back and forth to another similar data structure: a depthlist (is there another name for this?). For each leaf node / integer value in the `Snailfish` tree, represent that number as a pair `(value, depth)`. So 

{{< inline-latex "\langle \langle 1, \langle 2, \langle 3, 4 \rangle \rangle \rangle, 5 \rangle" >}} would be `[(1, 2), (2, 3), (3, 4), (4, 4), (5, 1)]`. 

```python
@dataclass(frozen=True)
class Snailfish():
    ...

    def to_depthlist(self) -> List[Tuple[int, int]]:
        '''Convert to list of (value, depth).'''

        def g(sf: Union[int, 'Snailfish'], depth: int) -> Generator[Tuple[int, int], None, None]:
            if isinstance(sf, int):
                yield (sf, depth)
            else:
                yield from g(sf.left, depth + 1)
                yield from g(sf.right, depth + 1)

        return list(g(self, 0))
```

Converting back is a bit trickier, but actually similar to parsing (repeatedly combine pairs at the same depth until everything is combined):

```python
@dataclass(frozen=True)
class Snailfish():
    ...

    @staticmethod
    def from_depthlist(dls: List[Tuple[int, int]]) -> 'Snailfish':
        '''Convert from a list of (value, depth).'''

        # To make typing happy, copy to a list that can have either
        mixedls: List[Tuple[Union[int, 'Snailfish'], int]] = [
            (value, depth)
            for (value, depth)
            in dls
        ]

        while len(mixedls) > 1:
            for index, ((left, left_depth), (right, right_depth)) in enumerate(zip(mixedls, mixedls[1:])):
                if left_depth == right_depth:
                    mixedls[index] = (Snailfish(left, right), left_depth - 1)
                    del mixedls[index+1]

                    break

        assert isinstance(mixedls[0][0], Snailfish)
        return mixedls[0][0]
```

Using this data structure, it's much easier to deal with `explode`:

* Find the first pair of numbers with the same depth (`4` in this case) that are deep enough
* Move the two values over one each
* Add a `0` at `depth-1`

And splitting is just as easy:

* Find the value to split, replace it with two nodes (ceiling and floor of division by 2)

```python
@dataclass(frozen=True)
class Snailfish():
    ...

    def reduce(self) -> 'Snailfish':
        '''Convert this snailfish to minimum form using the result for explosing and splitting.'''

        # Much easier to work with mutable depthlists...
        dls = self.to_depthlist()

        reducing = True
        while reducing:
            reducing = False
            logging.debug(f'Reducing: dls={dls}, sf={Snailfish.from_depthlist(dls)}')

            # Check for any pairs that needs exploding
            for index, (value, depth) in enumerate(dls):
                if depth > 4 and index < len(dls) - 1 and depth == dls[index + 1][1]:
                    logging.debug(f' - Exploding at {index=} with {value=} and {depth=}')

                    prefix = dls[:index]
                    infix = [(0, depth-1)]
                    suffix = dls[index+2:]

                    # Increase the previous value by one (if it exists)
                    if prefix:
                        prefix[-1] = (prefix[-1][0] + value, prefix[-1][1])

                    # Increase the next value by one (if it exists)
                    if suffix:
                        suffix[0] = (suffix[0][0] + dls[index+1][0], suffix[0][1])

                    dls = prefix + infix + suffix

                    reducing = True
                    break

            if reducing:
                continue

            # If not exploding, check for any value that needs splitting
            for index, (value, depth) in enumerate(dls):
                if value >= 10:
                    logging.debug(f' - Splitting at {index=} with {value=}')

                    dls = (
                        dls[:index]
                        + [
                            (math.floor(value / 2), depth + 1),
                            (math.ceil(value / 2), depth + 1),
                        ]
                        + dls[index+1:]
                    )

                    reducing = True
                    break

        return Snailfish.from_depthlist(dls)
```

It's a bit messy, but it works great. 

And now that we have all that... we can actually do the problem.

```python
def part1(file: typer.FileText):

    sum: Optional[Snailfish] = None

    while sf := Snailfish.read(file):
        logging.info(f'Adding: {sf} to {sum}')
        assert isinstance(sf, Snailfish)

        if sum is None:
            sum = sf
        else:
            sum += sf

    assert sum is not None

    logging.info(f'Final result: {sum}')
    print(sum.magnitude())
```

Neat:

```bash
$ python3 pairs-of-pairs.py part1 input.txt
4433
# time 443584917ns / 0.44s
```

That was a ... very strange/convoluted problem, but it was an interesting example of why data structures (and being able to convert between one another) is worthwhile. 

#### **Part 2:** Find the pair of Snailfish numbers in your input with the largest magnitude of their sums.

I'm not sure there's a better way that just brute forcing it:

```python
def part2(file: typer.FileText):

    sfes: List[Snailfish] = []
    while sf := Snailfish.read(file):
        assert isinstance(sf, Snailfish)
        sfes.append(sf)

    print(max(
        (sf1 + sf2).magnitude()
        for sf1 in sfes
        for sf2 in sfes
        if sf1 != sf2
    ))
```

And it works fine:

```bash
$ python3 pairs-of-pairs.py part2 input.txt
4559
# time 5653670916ns / 5.65s
```

It's a bit slower than I'd like... but I have spent far more than enough time on this problem... 
