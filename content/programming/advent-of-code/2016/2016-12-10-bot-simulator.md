---
title: "AoC 2016 Day 10: Bot Simulator"
date: 2016-12-10
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2016
---
### Source: [Balance Bots](http://adventofcode.com/2016/day/10)

> **Part 1:** Create a sorting machine using input of the following form:

> - `value X goes to bot A` - an input to bot `A`
> - `bot A gives low to (bot|output) B and high to (bot|output) C` - a sorter that takes two inputs and sends them to the specified bots or output channels

> Find the bot that compares the values `17` and `61`.

<!--more-->

A bit of an odd problem. The bots sound like self contained entities, so we'll create a class for them:

```python
class Bot(object):
    cache = {}

    def __init__(self, name):
        self.name = name
        self.values = set()
        self.low_output = None
        self.high_output = None
        self.compared = []

        if args.debug:
            print('{} created'.format(self))

    @staticmethod
    def get(name):
        if not name in Bot.cache:
            Bot.cache[name] = Bot(name)

        return Bot.cache[name]

    @staticmethod
    def all():
        for name in sorted(list(Bot.cache.keys())):
            yield Bot.get(name)

    def __str__(self):
        return 'Bot<{name}, {values}, low:{low_output}, high:{high_output}>'.format(
            name = self.name,
            values = list(sorted(self.values)),
            low_output = self.low_output,
            high_output = self.high_output,
        )

    def give(self, value):
        if args.debug:
            print('{} given {}'.format(self, value))

        self.values.add(value)

        if len(self.values) == 2:
            self.compared.append(set(self.values))

            if not self.low_output or not self.high_output:
                #raise Exception('{} got a second value but has not output'.format(self))
                print('{} got a second value but has not output'.format(self))
                return

            Bot.get(self.low_output).give(min(self.values))
            Bot.get(self.high_output).give(max(self.values))

            self.values.clear()
```

After that, we can use regular expressions to parse the input:

```python
re_value = re.compile(r'value (?P<value>\d+) goes to (?P<name>(?:(bot|output)) (\d+))')
re_mapping = re.compile(r'(?P<input>(?:(bot|output)) (\d+)) gives low to (?P<low_output>(?:(bot|output)) (\d+)) and high to (?P<high_output>(?:(bot|output)) (\d+))')

values = list()

with open(args.input, 'r') as fin:
    for line in fin:
        if args.debug:
            print(line.strip())

        m_value = re_value.match(line)
        m_mapping = re_mapping.match(line)

        if m_value:
            values.append((m_value.group('name'), int(m_value.group('value'))))

        elif m_mapping:
            input = m_mapping.group('input')
            low_output = m_mapping.group('low_output')
            high_output = m_mapping.group('high_output')

            Bot.get(input).low_output = low_output
            Bot.get(input).high_output = high_output
```

Now that the chain of bots is set up, we can send in the input values and then check which bots compared what:

```python
for name, value in values:
    Bot.get(name).give(value)

for bot in Bot.all():
    if set(args.targets) in bot.compared:
        print(bot, 'compared', args.targets)
```

This specifically needs to happen after all of the bots are set up, since you cannot output to a bot if you haven't see the input before the bots definition. That's why the values are cached in `values`.

A neat little bit of code.

> **Part 2:** What is the product `output0 * output1 * output2`?

I'm actually just simulating outputs as bots that are named `output`, so find the final values of those:

```python
print('output0 * output1 * output2 = {}'.format(
    list(Bot.get('output 0').values)[0]
    * list(Bot.get('output 1').values)[0]
    * list(Bot.get('output 2').values)[0]
))
```

And that's it.

A neat simulation.
