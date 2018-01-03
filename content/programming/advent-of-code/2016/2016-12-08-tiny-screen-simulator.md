---
title: "AoC 2016 Day 8: Tiny Screen Simulator"
date: 2016-12-08
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2016
---
### Source: [Two-Factor Authentication](http://adventofcode.com/2016/day/8)

> **Part 1:** Implement a 50x6 pixel screen with the following commands:

> - `rect AxB` turn on a rectangle of pixels in the top left corner
> - `rotate row y=A by B` rotates row `A` right by `B` pixels
> - `rotate column x=A by B` rotates column `A` down by `B` pixels

> After a given sequence of commands, how many pixels are on?

<!--more-->

Let's make this one object oriented:

```python
class Screen(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.data = [([False] * self.width) for i in range(self.height)]

    def __str__(self):
        return 'Screen<{}, {}>\n{}'.format(
            self.width,
            self.height,
            '\n'.join(''.join(('#' if el else '-') for el in row) for row in self.data),
        )

    def __len__(self):
        return sum(
            (1 if self[x, y] else 0)
            for x in range(self.width)
            for y in range(self.height)
        )

    def __getitem__(self, pt):
        (x, y) = pt
        return self.data[y % self.height][x % self.width]

    def __setitem__(self, pt, value):
        (x, y) = pt
        self.data[y % self.height][x % self.width] = value
```

This will allow us to use `len(screen)` to determine the number of lit pixels and `screen[x, y] = True` to turn on pixels[^1].

With that, we can implement drawing and use `len` for the final answer:

```python
screen = Screen(args.width, args.height)

with open(args.input, 'r') as fin:
    for line in fin:
        print(line)

        m_rect = re_rect.match(line)
        m_rotate = re_rotate.match(line)

        if m_rect:
            for x in range(int(m_rect.group('width'))):
                for y in range(int(m_rect.group('height'))):
                    screen[x, y] = True

        elif m_rotate:
            offset = int(m_rotate.group('offset'))
            index = int(m_rotate.group('index'))

            if m_rotate.group('mode') == 'column':
                new_data = [screen[index, y + yd] for yd in range(screen.height)]
                for yd in range(screen.height):
                    screen[index, y + yd + offset] = new_data[yd]
            else:
                new_data = [screen[x + xd, index] for xd in range(screen.width)]
                for xd in range(screen.width):
                    screen[x + xd + offset, index] = new_data[xd]

        print(screen)
        print()

print('active cells', len(screen))
```

> **Part 2:** What is the screen displaying?

I didn't actually automate this one (although it's certainly possible). Instead, I just printed out the current screen, which shows a string of capital letters in a minimal font:

```text
> $ python3 tiny-screen-simulator.py input.txt

...

Screen<50, 6>
-##--####-#----####-#-----##--#---#####--##---###-
#--#-#----#----#----#----#--#-#---##----#--#-#----
#----###--#----###--#----#--#--#-#-###--#----#----
#----#----#----#----#----#--#---#--#----#-----##--
#--#-#----#----#----#----#--#---#--#----#--#----#-
-##--#----####-####-####--##----#--#-----##--###--

active cells 106
```

That's actually pretty cool. I wonder how hard it would be to write a script to generate a minimal set of commands to generate text like that? 

[^1]: How does that work? It turns out that the comma creates tuples, not the paranthesis. So `screen[x, y]` is calling `Screen.__getitem__` and passing a single argument[^2]: `(x, y)`.
[^2]: Other than `self` of course.
