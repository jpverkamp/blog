---
title: "AoC 2017 Day 8: Conditiputer"
date: 2017-12-08
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Assemblers
- Virtual Machines
series:
- Advent of Code 2017
---
### Source: [I Heard You Like Registers](http://adventofcode.com/2017/day/8)[^yo]

> **Part 1:** Given a set of registers initialized to 0, interpret a series of instruction of the form:

> - `{register} (inc|dec) {number|register} if {number|register} (<|<=|=|!=|=>|>) {number|register}`

> What is the largest value in any register?

<!--more-->

In order to make the code here a bit more elegant, we're going to want to use the {{< doc python operator >}} module:

```python
conditionals = {
    '<': operator.lt,
    '<=': operator.le,
    '==': operator.eq,
    '!=': operator.ne,
    '>=': operator.ge,
    '>': operator.gt,
}
```

Also, we want a helper function that can take either a number or register and return either that number or the value of that register[^EAFP]:

```python
def val(x):
    try:
        return int(x)
    except:
        return registers[x]
```

Now that we have that, we can apply the commands. We'll use regular expression to parse the inputs and apply the `conditionals` above:

```python
registers = collections.defaultdict(lambda : 0)

for line in lib.input():
    register, mode, value, _, left, op, right = line.split()

    f = conditionals[op]

    if f(val(left), val(right)):
        if mode == 'inc':
            registers[register] += val(value)
        else:
            registers[register] -= val(value)

print(max(registers.values()))
```

If we didn't have the {{< doc python operator >}} module, we'd have a large `if/elif/else` block instead. I like this better; [[wiki:higher order functions]]() are lovely.

> **Part 2:** What is the largest value any register reaches during execution?

To track this, we just need to keep a variable that will track the `max_register_value` as we go:

```python
max_register_value = 0
for line in lib.input():
    ...

    max_register_value = max(max_register_value, *registers.values())

print('maximums, final: {}, overall: {}'.format(
    max(registers.values()),
    max_register_value,
))
```

The `*` operator[^splat] allows you to send each of the `values` in the registers into the `max` function as parameters, which is nice.

This is another case where there's not much point in running the two parts individually:

```bash
$ python3 run-all.py day-08

day-08  python3 conditiputer.py input.txt       0.11300992965698242     maximums, final: 6012, overall: 6369
```

[^yo]: Yo dawg.
[^EAFP]: It's Easier to Ask Forgiveness than Permission.
[^splat]: Splat. :smile:
