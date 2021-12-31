---
title: "AoC 2021 Day 6: We All Glow Down Here"
date: 2021-12-06 00:00:10
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
programming/topics:
- Cellular Automata
- Generative Art
---
### Source: [Latternfish](https://adventofcode.com/2021/day/6)

#### **Part 1:** Simulate a population of lanternfish. Each fish is immortal, starts having children after 9 days, and has another child after 7 more days. Calculate the number of fish after 80 days.

<!--more-->

I can almost guarantee that part 2 will be scaling up significantly, so the obvious answer of keeping a list of ages and simulating each will... probably get very slow. Instead, we don't care at all about individual fish, let's just keep their ages:

```python
class School:
    '''Represents a school of fish.'''

    def __init__(self, fish):
        '''Loads the given list of fish into a map of ages.'''

        self.data = {
            age: 0
            for age in range(9)
        }

        for each in fish:
            self.data[each] += 1

    @staticmethod
    def from_file(file: TextIO):
        '''Load a school from a file-like object'''

        fish = [
            int(age)
            for line in file
            for age in line.split(',')
        ]

        return School(fish)

    def step(self):
        '''
        Advance this school 1 day.

        All fish increase in age by 1 tick
        Fish that are of a spawning age reset to 7 days to spawn and create a new 9 day to spawn fish. 

        Remember 0 based indexing.
        '''

        # Remember how many fish are going to spawn
        breeding = self.data[0]

        # Increase age of each fish by 1
        for age in range(1, 9):
            self.data[age - 1] = self.data[age]

        # Each fish that spawns moves to age 6 (don't overwrite previously age 7) and spawns a new one of age 8
        self.data[6] += breeding
        self.data[8] = breeding

    def __str__(self):
        '''Return a comma-delimited list of fish ages.'''

        return ','.join(
            str(age)
            for age, qty in self.data.items()
            for _ in range(qty)
        )

    def size(self):
        '''Return the number of fish in the school.'''

        return sum(qty for age, qty in self.data.items())
```

That really handles it. Most of it is bookkeeping: loading in the fish from a file, printing them nicely, and counting the `len` / number of fish. The interesting bit is `step`, where we have to be a little careful with ages:

- All fish age 1-8 increase in age 1 step (which means they are one step closer to breeding age)
- All fish age 0 revert to age 6 (which means 6 steps to breeding age) plus spawn a new one

If we count up, that means each number overwrites the one we've already done, which is fine. 

And... that's all we really need:

```python
@app.command()
def main(ticks: int, file: typer.FileText):
    school = School.from_file(file)

    for i in range(ticks):
        school.step()

    print(school.size())
```

Run it for 80:

```bash
$ python3 we-all-glow-down-here.py 80 input.txt
395627
```

Fin. 

#### **Part 2:** Run the simulation for 256 days.

:smile: 

Called it.

```bash
$ python3 we-all-glow-down-here.py 256 input.txt
1767323539209
```

And it's barely any slower:

```bash
$ python3 we-all-glow-down-here.py 80 input.txt
395627
# time 38854250ns / 0.04s

$ python3 we-all-glow-down-here.py 256 input.txt
1767323539209
# time 38013958ns / 0.04s
```

Since the time to simulate is mostly taken up with loading/saving, the actual iterations are fast. Heck:

```python
$ time python3 we-all-glow-down-here.py 1000000 input.txt

11251...59768
1.12e37838

________________________________________________________
Executed in    3.22 secs    fish           external
   usr time    3.13 secs   55.00 micros    3.13 secs
   sys time    0.03 secs  652.00 micros    0.03 secs
```

1 MILLION generations in 3 seconds. I did add this to print the scientific notation:

```python
size_string = str(school.size())
print(f'{size_string[0]}.{size_string[1:3]}e{len(size_string)}')
```

I tried to use `f{school.size():e}` first, but... 

```python
>>> print(f{school.size():e})
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
OverflowError: int too large to convert to float

>>> 1e37838
inf
```

Yeah. It's too big for floating point numbers. Fun times!


#### Fun (subtle) problems with types

So this was an interesting error:

```python
Traceback (most recent call last):
  File "/Users/jp/Projects/advent-of-code/2021/06/we-all-glow-down-here.py", line 85, in <module>
    app()
  File "/opt/homebrew/lib/python3.9/site-packages/typer/main.py", line 214, in __call__
    return get_command(self)(*args, **kwargs)
  File "/opt/homebrew/lib/python3.9/site-packages/click/core.py", line 829, in __call__
    return self.main(*args, **kwargs)
  File "/opt/homebrew/lib/python3.9/site-packages/click/core.py", line 782, in main
    rv = self.invoke(ctx)
  File "/opt/homebrew/lib/python3.9/site-packages/click/core.py", line 1066, in invoke
    return ctx.invoke(self.callback, **ctx.params)
  File "/opt/homebrew/lib/python3.9/site-packages/click/core.py", line 610, in invoke
    return callback(*args, **kwargs)
  File "/opt/homebrew/lib/python3.9/site-packages/typer/main.py", line 500, in wrapper
    return callback(**use_params)  # type: ignore
  File "/Users/jp/Projects/advent-of-code/2021/06/we-all-glow-down-here.py", line 81, in main
    print(len(school))
OverflowError: cannot fit 'int' into an index-sized integer
```

Any guesses? 

It's a bit subtle, but the problem is that `len` has to return an 'index-sized integer', not just any int. So once the size gets too large, I couldn't use `__len__` for the size of the school any more and why I changed to a `.size()` function instead.