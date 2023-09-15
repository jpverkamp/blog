---
title: "AoC 2017 Day 9: Garbage Gobbler"
date: 2017-12-09
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Lexing
- Parsing
series:
- Advent of Code 2017
---
### Source: [Stream Processing](http://adventofcode.com/2017/day/9)

> **Part 1:** An input stream can contain:

> - `groups` are delimited by `{` and `}`, `groups` are nestable and may contain `garbage` or data (objects within a `group` are [[wiki:comma delimited]]())
> - `garbage` is delimited by `<` and `>`, `groups` cannot be nested within `garbage`, a `!` within `garbage` is an [[wiki:escape character]](): `!>` does not end a garbage segment

> The score of a single group is equal to how many times it is nested (the innermost group of `{{{}}}` has score `3`).

> The score of a stream is the sum of the scores of all groups in that stream.

> What is the total score of your input?

<!--more-->

Since the `groups` can be nested, they can't[^doOrDoNot] be parsed with [[wiki:regular expressions]](). The language is relatively simple enough that we could directly write a [[wiki:text="parser" page="Parsing#Computer_languages"]]() (keeping a stack of how deep we are currently nested in `groups`), but this sounds like a wonderful excuse to use the [PyParsing](http://pyparsing.wikispaces.com/) module:

First, we want to define `garbage`, since it cannot have anything nested in it. Garbage works essentially like a string:

```python
garbage = pp.Suppress(pp.QuotedString('<', escChar = '!', endQuoteChar='>'))
```

And then `groups` can contain either nested `groups`, `garbage`, or data:

```python
group = pp.Forward()
data = pp.Regex(r'[^}]+')

group << pp.Group(
    pp.Suppress('{')
    + pp.Optional(pp.delimitedList(group | garbage | data))
    + pp.Suppress('}')
)
```

We have to use [Forward](https://pythonhosted.org/pyparsing/pyparsing.Forward-class.html) since `groups` can be nested within themselves.

With those definitions, we can put together a parsing function:

```python
def parse(stream):
    '''Implement a pyparsing parser for the stream format.'''

    group = pp.Forward()
    garbage = pp.Suppress(pp.QuotedString('<', escChar = '!', endQuoteChar='>'))
    data = pp.Regex(r'[^}]+')

    group << pp.Group(
        pp.Suppress('{')
        + pp.Optional(pp.delimitedList(group | garbage | data))
        + pp.Suppress('}')
    )

    parser = (group | garbage)

    data = parser.parseString(stream)
    if data:
        return data[0]
```

Now that we can parse the data, we can score it recursively:

```python
def score_groups(data, depth = 1):
    '''
    The score of a group is equal to its depth.
    The score of data is equal to the sum of its groups.
    '''

    if isinstance(data, pp.ParseResults):
        data = data.asList()

    if isinstance(data, list):
        return depth + sum(score_groups(el, depth + 1) for el in data)
    else:
        return 0

total_score = 0

for line in lib.input():
    data = parse(line)
    total_score += score_groups(data)

print(total_score)
```

It's a bit complicated since PyParsing returns a custom object from the parser, but we can turn it to a list with `asList`.

> **Part 2:** How many non-escaped garbage characters are there in your input?

This got more exciting than I expected since `PyParsing.QuotedString` doesn't contain the escape characters, so we don't actually know how many characters were escaped. That's not at all what we want. So we have to write a custom parsing function. Since `garbage` cannot be nested, we can use regular expressions. To keep a count, I'm just going to use a global variable. So sue me. :smile:

```python
_last_garbage_count = 0

def parse(stream):
    '''Implement a pyparsing parser for the stream format.'''

    global _last_garbage_count
    _last_garbage_count = 0

    group = pp.Forward()
    garbage = pp.Suppress(pp.Regex(r'<([^!>]|!.)*>').setParseAction(count_garbage))
    data = pp.Regex(r'[^}]+')

    group << pp.Group(
        pp.Suppress('{')
        + pp.Optional(pp.delimitedList(group | garbage | data))
        + pp.Suppress('}')
    )

    parser = (group | garbage)
    data = parser.parseString(stream)
    if data:
        return data[0]

total_score = 0
total_garbage = 0

for line in lib.input():
    data = parse(line)

    count = count_groups(data)
    score = score_groups(data)
    total_score += score

    total_garbage += _last_garbage_count

print('score: {}, garbage: {}'.format(total_score, total_garbage))
```

It's a big ugly (with the global variable), but so it goes.

```bash
$ python3 run-all.py day-09

day-09  python3 garbage-gobbler.py input.txt    0.5247189998626709      score: 16021, garbage: 7685
```

[^doOrDoNot]: Well... shouldn't. If you know ahead of time how deep the groups are going to be nested in practice, it's possible. Ugly. But possible.
