---
title: "AoC 2016 Day 3: Triangle Validator"
date: 2016-12-03
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2016
---
### Source: [Squares With Three Sides](http://adventofcode.com/2016/day/3)

> **Part 1:** Given a list of sides, determine how many form valid triangles. (Hint: {{< wikipedia "triangle inequality" >}})

<!--more-->

Nothing particularly complicated about this one:

```python
possible_triangles = 0

with open(args.input_file, 'r') as fin:
    for line in fin:
        sides = list(sorted(map(int, line.split())))
        if sides[0] + sides[1] > sides[2]:
            possible_triangles += 1

print('part 1:', possible_triangles)
```

The most interesting part is probably sorting the sides so that you know the largest will always be `sides[2]`.

> **Part 2:** Reorder the sides so that each triangle is three numbers in a column. For example:

> ```
A B C
D E F
G H I
J K L
M N O
P Q R
...
```

> The triangles would be `ADG`, `BEH`, `CFI`, `JMP`, etc.

This mostly comes down to figuring out how to read the data in. In order to use mostly the same loop as before, I wrote a {{< doc python generator >}} that would read in three lines at a time into a buffer and then {{< doc python yield >}} the triangles from those three rows before reading the next:

```python
possible_triangles = 0

def rotate(stream):
    while True:
        triple = []
        for i in range(3):
            row = stream.readline()
            if not row: return
            triple.append(list(map(int, row.split())))

        for row in range(3):
            yield list(sorted(triple[col][row] for col in range(3)))

with open(args.input_file, 'r') as fin:
    for sides in rotate(fin):
        if sides[0] + sides[1] > sides[2]:
            possible_triangles += 1

print('part 2:', possible_triangles)
```

An interesting problem in reading input files. To some extent, that's a lot of programming in real life: figuring out how to turn real world data into something you can actually analyze. 
