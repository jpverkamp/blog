---
title: "AoC 2021 Day 20: Enhancinator"
date: 2021-12-20 00:00:05
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
---
### Source: [Trench Map](https://adventofcode.com/2021/day/20)

#### **Part 1:** Given a 9->1 {{< wikipedia "cellular automota" >}} update function (take the pixel and 8 surrounding pixels as a 9-bit index into the function) and a binary image, apply the function twice and count the number of 'lit' pixels. Assume that the canvas is infinite. 

That was fun! 

First, we want to represent our two data structures. First, the image itself. Because it can be infinite, we're going to store both pixels we know about (`data`) and a single value for `infinity`. We won't end up with stripes reaching out in this particular case. In most function applications, `infinity` will stay either on or off. But there is an edge case where it will oscillate. I'll come back to that when we get there.

```python
Point = Tuple[int, int]

@dataclass(frozen=True)
class InfiniteBitmap:
    '''
    Store an infinitely large bitmap.
    
    data is 'known' values
    infinity is every other point off to infinity
    '''

    data: MutableMapping[Point, bool]
    infinity: bool

    @staticmethod
    def read(file: TextIO) -> 'InfiniteBitmap':
        '''Read an infinite bitmap from file. Assume unset bits (infinity) are False.'''

        logging.info('Reading infinity bitmap')

        data = {
            (x, y): c == '#'
            for y, line in enumerate(file)
            for x, c in enumerate(line.strip())
        }

        mid_x = max(x for x, _ in data) // 2
        mid_y = max(y for _, y in data) // 2

        return InfiniteBitmap({(x - mid_x, y - mid_y): bit for (x, y), bit in data.items()}, False)

    def __repr__(self):
        '''Return a much smaller representation.'''

        return f'InfiniteBinary<{self.infinity}, {len(self)}/{len(self.data)}, {self.bounds()}>'

    def __len__(self) -> int:
        '''Return the number of lit pixels (might be effectively infinite).'''

        if self.infinity:
            return sys.maxsize
        else:
            return sum(
                1 if self[p] else 0
                for p in self.data
            )

    def __getitem__(self, p: Point) -> bool:
        '''Get the value at a given point p (use infinity if the point isn't otherwise known).'''

        return self.data.get(p, self.infinity)

    def bounds(self) -> Tuple[int, int, int, int]:
        '''Return (minimum x, maximum x, minimum y, maximum y)'''

        return (
            min(x for x, _ in self.data) - 5,
            max(x for x, _ in self.data) + 5,
            min(y for _, y in self.data) - 5,
            max(y for _, y in self.data) + 5,
        )
```

Most of this is just reading the data. I did do one interesting bit in the `read` function, which was to 'recenter' the data. After reading, the range is (0, width), but I'd rather it be (-width/2, width/2) so that the center point is actually in the center. 

In addition, we went ahead and put a `__len__` function here: the number of lit pixels. 

Okay, next up, let's work on that mapping function. This is the bulk of the problem:

```python
BitIndex = List[bool]

NEIGHBORHOOD = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0), (0,  0), (1,  0),
    (-1,  1), (0,  1), (1,  1),
]

@dataclass(frozen=True)
class BinaryMapping:
    '''Store a mapping from 9-bit values to 1-bit, loaded from a 512 character string of . (0) and # (1).'''

    map: List[bool]

    @staticmethod
    def read(file: TextIO):
        '''Read a BinaryMapping from an input stream.'''

        logging.info('Reading binary mapping')

        return BinaryMapping([c == '#' for c in file.readline().strip()])

    def __repr__(self):
        '''Return a unique representation of this map.'''

        binary = ''.join('1' if bit else '0' for bit in self.map)
        integer = int(binary, 2)
        bytes = integer.to_bytes(64, 'big')
        b64 = base64.b64encode(bytes).decode()

        return f'BinaryMapping<{b64}>'

    def __getitem__(self, k: Union[int, BitIndex]) -> bool:
        '''Get the value of the BinaryMapping by either integer index of a 9-bit binary BitIndex.'''

        if isinstance(k, int):
            return self.map[k]
        else:
            # TODO: Make this more efficient
            return self.map[int(''.join('1' if bit else '0' for bit in k), 2)]

    def __call__(self, bitmap: InfiniteBitmap) -> InfiniteBitmap:
        '''Apply this mapping to an infinite bitmap, generating a new one with this applied.'''

        logging.info(f'Calling {self} on {bitmap}')

        # Calculate the new infinity

        # If the lowest mapping is set, infinity goes from off to on
        # Likewise on the highest mapping for infinity from on to off
        if not bitmap.infinity and self[0]:
            new_infinity = True
        elif bitmap.infinity and not self[511]:
            new_infinity = False
        else:
            new_infinity = bitmap.infinity

        # Calculate all new points
        new_data = {}

        # Have to calculate all pixels one level out as well
        for x, y in bitmap.data:
            for xd, yd in NEIGHBORHOOD:
                # Don't calculate points more than once per update
                center = (x + xd, y + yd)
                if center in new_data:
                    continue

                neighbors = [
                    bitmap[x + xd + xd2, y + yd + yd2]
                    for xd2, yd2 in NEIGHBORHOOD
                ]

                new_value = self[neighbors]

                # If the value wasn't in the old map and matches the new infinity
                # We don't need to include it (prevent infinity expansion)
                if center in bitmap.data and new_value == new_infinity:
                    continue

                new_data[center] = new_value

        return InfiniteBitmap(new_data, new_infinity)
```

`__getitem__` will handle infinity (so we can always read any pixel, even if it's not already defined in the image). 

`__call__` is the core, it allows the function to be called on a `InfiniteBitmap` and returns the updated bitmap. Let's go through a few interesting points of it:

* Updating the infinite pixels: this is the edge case I was talking about earlier. If the first value in the update function (all false) returns true, we need to change infinite to true. Likewise if the last value is false, we need to make infinite false. If both of these are the case (as they are in my input), you'll get a flicker (see the rendering at the end). 

* Updating the majority of pixels
    * We need to update all pixels in the image *plus* all pixels adjacent to them, because those might change from off to on.
    * This would lead to infinitely growing memory... except we don't have to. If the new border pixel matches infinity, not setting it is fine, it will get rescanned on the edge update next time.

And that's, actually it!

Using the rendering function (we'll see at the end) and the test data, we can go from this:

{{< figure src="/embeds/2021/aoc2021-20-test-0000.png" >}}

To this:

{{< figure src="/embeds/2021/aoc2021-20-test-0001.png" >}}

To this:

{{< figure src="/embeds/2021/aoc2021-20-test-0002.png" >}}

It matches what we expect! A simple wrapper:

```python
def part1(file: typer.FileText):

    f = BinaryMapping.read(file)
    file.readline()
    bitmap = InfiniteBitmap.read(file)

    final_bitmap = f(f(bitmap))

    print(len(final_bitmap))
```

And run it:

```bash
$ python3 enhancinator.py part1 input.txt
5057
# time 290676167ns / 0.29s
```

Not bad!

<!--more-->

#### **Part 2:** Apply the same function 50 times and count the number of lit pixels.

So... this isn't actually anything harder:

```python
def part2(file: typer.FileText):
    f = BinaryMapping.read(file)
    file.readline()
    bitmap = InfiniteBitmap.read(file)

    for i in range(50):
        bitmap = f(bitmap)

    print(len(bitmap))
```

Just slower:

```bash
$ python3 enhancinator.py part2 input.txt
18502
# time 10267020083ns / 10.27s
```

A bit slower than I'd like, but I don't have a huge buildup I can do here. I could certainly use a bit more complicated code to avoid a lot of the Python packing/uppacking and indirection, but that would make the code a lot more complicated to read. So we'll keep it for now. 

#### Fun with rendering images

Let's render these images! We're already mostly there:

```python

@dataclass(frozen=True)
class InfiniteBitmap:
    ...

    def render(self, include_axis: bool = False) -> 'Image':
        '''Render this infinity bitmap as an image.'''

        from PIL import Image  # type: ignore

        min_x, max_x, min_y, max_y = self.bounds()
        width = max_x - min_x + 1
        height = max_y - min_y + 1

        WHITE = (255, 255, 255)
        BLACK = (0, 0, 0)
        GRAY = (127, 127, 127)

        image = Image.new('RGB', (width, height), WHITE)
        pixels = image.load()

        for x in range(width):
            for y in range(height):
                ix = x + min_x
                iy = y + min_y

                if self[ix, iy]:
                    pixels[x, y] = BLACK
                elif include_axis and (ix == 0 or iy == 0):
                    pixels[x, y] = GRAY

        return image
```

And a wrapper to render with some nice options:

```python
@app.command()
def render(file: typer.FileText, size: str, target: pathlib.Path, generations: int):

    from PIL import Image  # type: ignore

    f = BinaryMapping.read(file)
    file.readline()
    bitmap = InfiniteBitmap.read(file)

    try:
        width, height = [int(v) for v in size.split('x')]
    except:
        typer.echo('Unable to parse size, expecting a value like 400x400', err=True)
        raise typer.Exit(1)

    base_image = bitmap.render(True).resize((width, height), Image.NEAREST)

    rest_images = []
    for i in range(1, generations + 1):
        bitmap = f(bitmap)
        rest_images.append(bitmap.render(True).resize((width, height), Image.NEAREST))

    if str(target).lower().endswith('gif'):
        base_image.save(target, save_all=True, append_images=rest_images)
    else:
        for i, image in enumerate([base_image] + rest_images):
            image.save(str(target).format(i=i))
```

For the test input:

```bash
$ python3 enhancinator.py render test.txt 400x400 'aoc2021-20-test.gif' 100
```

{{< figure src="/embeds/2021/aoc2021-20-test.gif" >}}

That's pretty cool. What about my own input?

```bash
$ python3 enhancinator.py render input.txt 400x400 'aoc2021-20-input.gif' 100
```

{{< figure src="/embeds/2021/aoc2021-20-input.gif" >}}

Huh. Other than the flashing, that's not actually that cool. Eating away at the corner is interesting enough. I suppose it has to be generated for different users, so there's only so much you can do with it. So it goes. 

Now I wonder how long it takes to completely clear...

