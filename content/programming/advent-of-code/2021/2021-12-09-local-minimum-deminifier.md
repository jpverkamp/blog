---
title: "AoC 2021 Day 9: Local Minimum Deminifier"
date: 2021-12-09 00:00:15
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
programming/topics:
- Data Structures
- Graphics
---
### Source: [Smoke Basin](https://adventofcode.com/2021/day/9)

#### **Part 1:** Given a heightmap, find all local minimums. Return the sum of (minimum height + 1) for each local minimum. 

<!--more-->

First, as is often the case, let's load the data:

```python
def load(file: TextIO) -> MutableMapping[Tuple[int, int], int]:
    return {
        (x, y): int(height)
        for y, line in enumerate(file)
        for x, height in enumerate(line.strip())
    }
```

This could more efficiently have been stored in a 2D array, but I really like dicts of `point -> value` for this sort of thing. Especially because in Python you don't actually need the `()` for tuples in most cases, just the comma. So `heightmap[x,y]` works great. 

After we have that data, it's just a matter of checking each point to see if all 2/3/4 neighbors are larger than a specific point, while at the same time making sure that we don't run off the edge of the map.

```python
@app.command()
def part1(file: typer.FileText):

    heightmap = load(file)
    total_risk = 0

    for (x, y), height in heightmap.items():
        neighbor_heights = [
            heightmap.get((x + xd, y + yd), 10)
            for xd, yd in ORTHAGONAL_NEIGHBORS
        ]

        if min(neighbor_heights) > height:
            total_risk += height + 1

    print(f'{total_risk=}')
```

`ORTHAGONAL_NEIGHBORS = [(-1, 0), (1, 0), (0, -1), (0, 1)]`. And that's all we need:

```bash
$ python3 local-minimum-deminifier.py part1 input.txt
total_risk=491
```

#### **Part 2:** Calculate 'basins', regions of the heightmap surrounded by heights of 9. Return the product of the size of the three largest basins.

This one is a bit more interesting. We already have the heightmap and we don't actually currently care about the local minimums anymore. Instead, we want to find regions. For that, the algorithm of choice is a {{< wikipedia "flood fill" >}}. Specifically, we can get away with a {{< wikipedia "dynamic algorithm" >}} here:

* For each point in the heightmap:
    * If it's been assigned a height or is a wall (height of 9), ignore it
    * Otherwise, assign that point a height and floodfill from that point

To floodfill:

* Initialize a queue of points `L`, while `L` is not empty, take the next point `p` from `L`:
    * If `p` is off the map, a wall, or already processed, skip it
    * Otherwise, assign that point to the current flood fill and add all four of its neighbors to the list of points to check

This is a bit inefficient because we're adding the point we came from but because we only expand if we actually fill a point, it won't get stuck. 

Turning that into code:

```python
def part2(file: typer.FileText):

    heightmap = load(file)

    # A map (like heightmap) of Point -> which basin that point belongs to
    basinmap: MutableMapping[Tuple[int, int], int] = {}

    # A map of basin index to a set of points in that basin (to count size)
    basins: MutableMapping[int, MutableSet[Tuple[int, int]]] = {}

    def floodfill(x, y, value):
        to_visit = [(x, y)]
        basins[value] = set()

        while to_visit:
            x, y = to_visit.pop()

            # Ignore points out of bounds or with heights of 9
            if (x, y) not in heightmap or heightmap[x, y] == 9:
                continue

            # Don't fill a point twice
            if basinmap.get((x, y)):
                continue

            # Otherwise, fill it and recur
            #
            # This is a bit inefficient because we're adding the point we came from
            #   but because we only expand if we actually fill a point, it won't get stuck
            basinmap[x, y] = value
            basins[value].add((x, y))

            for xd, yd in ORTHAGONAL_NEIGHBORS:
                to_visit.append((x + xd, y + yd))

    # Flood fill from every non-9 point in the map
    next_value = 1
    for (x, y), height in heightmap.items():
        # Ignore 9s and anything that already has a value
        if height == 9 or (x, y) in basinmap:
            continue

        # If we made it this far, floodfill the next basin and increment
        floodfill(x, y, next_value)
        next_value += 1

    # Find the size of the largest three basins
    sizes = list(reversed(sorted(len(points) for _, points in basins.items())))
    product = sizes[0] * sizes[1] * sizes[2]

    print(f'The largest basins are {sizes[:3]} with a size product of {product}')
```

That just seems... fairly elegant. I like it.

```bash
$ python3 local-minimum-deminifier.py part2 input.txt
The largest basins are [112, 99, 97] with a size product of 1075536
```

It's plenty fast enough too:

```bash
$ python3 local-minimum-deminifier.py part1 input.txt
total_risk=491
# time 45522958ns / 0.05s

$ python3 local-minimum-deminifier.py part2 input.txt
The largest basins are [112, 99, 97] with a size product of 1075536
# time 46223083ns / 0.05s
```

#### Viewing the heightmaps

One thing that I wanted to do was visualize what the map looked like. [Pillow](https://pillow.readthedocs.io/en/stable/) to the rescue!

First, the heightmap itself:

```python
from PIL import Image

heightmap = load(file)
image_width = max(x for (x, _) in heightmap) + 1
image_height = max(y for (_, y) in heightmap) + 1

# Generate a grayscale map of heights from the given image
heightmap_image = Image.new('HSV', (image_width, image_height))
heightmap_data = heightmap_image.load()

for (x, y), height in heightmap.items():
    heightmap_data[x, y] = (0, 0, 255 * height // 10)

heightmap_image = heightmap_image.resize((image_width * 4, image_height * 4), Image.NEAREST)
heightmap_image.convert(mode='RGB').save(heightmap_file)
```

{{< figure src="/embeds/2021/aoc2021-09-heightmap.png" >}}

I guess I expected something more interesting. :) But having it be randomly generated works. Next, the basins:

```python
# Generate a map of all of the basins in the image
basinmap_image = Image.new('HSV', (image_width, image_height))
basinmap_data = basinmap_image.load()

basins = find_basins(heightmap)

for index, points in basins.items():
    for (x, y) in points:
        basinmap_data[x, y] = ((10007 * index // len(basins)) % 255, 255, 255)

basinmap_image = basinmap_image.resize((image_width * 4, image_height * 4), Image.NEAREST)
basinmap_image.convert(mode='RGB').save(basin_file)
```

I used {{< wikipedia "HSV" >}} so that I could index colors based on the basin index and then 10007 as a big prime to scramble them a bit so it wasn't just a nice color map descending the image (because of the order I flood filled them in). 

{{< figure src="/embeds/2021/aoc2021-09-basins.png" >}}

Finally, just color the biggest three:

```python
# Only draw the 3 largest basins
biggest_basins = [
    index
    for _, index in list(reversed(sorted(
        (len(points), index)
        for index, points in basins.items()
    )))[:3]
]

biggest_basin_image = Image.new('HSV', (image_width, image_height))
biggest_basin_data = biggest_basin_image.load()

basins = find_basins(heightmap)

for index, points in basins.items():
    for (x, y) in points:
        if index in biggest_basins:
            biggest_basin_data[x, y] = ((10007 * index // len(basins)) % 255, 255, 255)
        else:
            biggest_basin_data[x, y] = (0, 0, 255)

biggest_basin_image = biggest_basin_image.resize((image_width * 4, image_height * 4), Image.NEAREST)
biggest_basin_image.convert(mode='RGB').save(largest_basin_file)
```

{{< figure src="/embeds/2021/aoc2021-09-big-basins.png" >}}

Necessary? No. Fun? Yes!