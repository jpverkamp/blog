---
title: "AoC 2021 Day 14: Polymerizationinator"
date: 2021-12-14
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
---
### Source: [Extended Polymerization](https://adventofcode.com/2021/day/14)

#### **Part 1:** Given a complete function `f(a, b) -> c` where any string `ab` becomes `acb` and an input string, apply the function at the same time to every (overlapping) pair of letters. Repeat this time times. Report the difference in counts between the most and least common letters in the final situation. 


Okay. First try, let's just solve this directly. Although, since we know that we're going to be inserting into the middle of the list constantly, we can be slightly more efficient by using a {{< wikipedia "linked list" >}}:

```python

PolyMap = Mapping[Tuple[str, str], str]


@dataclass
class Node(Iterable):
    value: str
    next: Optional['Node']

    def expand_via(self, map: PolyMap) -> 'Node':
        if self.next is None:
            return self

        for a, b in zip(self, self.next):
            if (a.value, b.value) in map:
                a.next = Node(map[a.value, b.value], b)

        return self

    @staticmethod
    def from_iter(iter: Iterable) -> 'Node':
        head = None
        previous = None

        for el in iter:
            n = Node(el, None)

            if previous:
                previous.next = n
            else:
                head = n

            previous = n

        return head

    def __iter__(self):
        self.iter_node = self
        return self

    def __next__(self):
        if not self.iter_node:
            raise StopIteration

        result = self.iter_node
        self.iter_node = self.iter_node.next
        return result

    def __str__(self):
        return ''.join(self)

def load(file: TextIO) -> Tuple[Node, PolyMap]:

    ls = Node.from_iter(file.readline().strip())
    file.readline()

    map = {
        (line[0], line[1]): line[6]
        for line in file
    }

    return ls, map

```

Okay, there are basically three interesting parts here. 

* First, the `from_iter` function. That will take any `iterable` and make a linked list out of it, returning the head of that list. It does this by creating each Node in turn and attaching it to the previously created node.

* Next, the `__iter__` and `__next__` functions. Together, these make `Node` iterable, so that we can do things like `for n in ls: ...` where `ls` is the head of a linked list. 

* Finally, `expand_via`. That will take in a mapping of pairs to a single character and expand the current linked list with it. Specifically, for any characters `a` and `b` in the linked list, insert a new node between them with value `map[a, b]`. Pretty cool right? 

* While we're at it, add a function to `load` the puzzle definitions from a file: the initial linked list (a string is iterable) and the series of mappings. They're always single characters in a set format, so we can hardcode where they are in the string. Perfect? No. Workable for now, sure.  

With all that, we can write a direct solution to the puzzle:

```python

@app.command()
def direct(file: typer.FileText, steps: int):
    ls, map = load(file)

    import time
    start = time.time()

    for i in range(steps):
        logging.info(f'Generation {i} calculate after {time.time() - start:02f} sec, has {len(list(ls))} elements')
        ls.expand_via(map)

    counts = Counter(n.value for n in ls)
    logging.info(f'{counts=}')

    most, _ = max((qty, c) for (c, qty) in counts.items())
    least, _ = min((qty, c) for (c, qty) in counts.items())

    print(most - least)
```

(There's a reason I named this `direct` rather than `part1`) 

It actually works great:

```bash
$ python3 polymerizationinator.py direct input.txt 10
2797
```

So that's all she wrote, right? 

Well...

<!--more-->

#### **Part 2:** Do the same for 40 iterations (instead of 10). 

Okay. We have a problem. 


```bash
$ python3 polymerizationinator.py direct input.txt 10
2797
# time 76895250ns / 0.08s

$ python3 polymerizationinator.py direct input.txt 11
5437
# time 77964125ns / 0.08s

$ python3 polymerizationinator.py direct input.txt 12
10672
# time 123601208ns / 0.12s

$ python3 polymerizationinator.py direct input.txt 13
21340
# time 212642208ns / 0.21s

$ python3 polymerizationinator.py direct input.txt 14
42836
# time 409988583ns / 0.41s

$ python3 polymerizationinator.py direct input.txt 15
85972
# time 795902958ns / 0.80s

$ python3 polymerizationinator.py direct input.txt 16
172844
# time 1567806500ns / 1.57s

$ python3 polymerizationinator.py direct input.txt 17
347059
# time 3146193833ns / 3.15s

$ python3 polymerizationinator.py direct input.txt 18
696285
# time 6848070667ns / 6.85s

$ python3 polymerizationinator.py direct input.txt 19
1395343
# time 12827071459ns / 12.83s

$ python3 polymerizationinator.py direct input.txt 20
2793845
# time 35055311792ns / 35.06s
```

It's quick enough at small problems, but as they mentioned in the problem, it grows exponentially. Each iteration we add roughly doubles the time. And we're already up to 35 seconds after just 20. To double that another 20 times... we're talking a runtime of roughly a year. I'm... not going to wait that long. Instead, let's try something totally different. Rather than actually calculate the strings, we're going to recursively calculate how *many* of each value there are for any given pair of letters and how far we still need to split them. 

```python
def recursive(file: typer.FileText, steps: int):
    ls, map = load(file)

    # Recursively count all elements that will be returned from the character pair a,b at depth
    # This will use the mapping specified in map above
    # This will recur depth += 1 each time until depth = steps (so will always terminate)
    def count(a, b, depth):
        logging.info(f'{" " * depth} > count({a}, {b}, {depth})')

        if depth == steps:
            result = {a: 1}
        else:
            result = {}

            for left, right in [(a, map[a, b]), (map[a, b], b)]:
                for k, v in count(left, right, depth + 1).items():
                    result[k] = result.get(k, 0) + v

        logging.info(f'{" " * depth} < count({a}, {b}, {depth}) = {result}')
        return result

    # Recursively figure out the counts for each pair of elements
    # The rightmost element is never counted, so add it at the end
    counts: MutableMapping[str, int] = {}
    if ls.next is not None:
        for a, b in zip(ls, ls.next):
            for k, v in count(a.value, b.value, 0).items():
                counts[k] = counts.get(k, 0) + v
        counts[b.value] = counts.get(b.value, 0) + 1

    logging.info(f'{counts=}')

    most, _ = max((qty, c) for (c, qty) in counts.items())
    least, _ = min((qty, c) for (c, qty) in counts.items())

    print(most - least)
```

The entire strength of this function is the `count` helper function. Like I said (both above and in the comment), this will take a pair of letters (the `a` and `b`) and a current depth and it will guarantee that it will return the total count of each letter in the final output between that `a` and `b` (including the `a`, but not the `b`, I'll come back to that). 

With that guarantee, that means that we can use the function recursively. We know that if we have `count(a, b, 1)` and the mapping `map[a, b] = c`, that means that we can guarantee: 

{{< latex >}}
count(a, b, n) = count(a, map(a, b), n+1) + count(map(a, b), b, n+1)
{{</ latex >}}

Since `n` is always increasing and we have a base case of `n` = the final depth, our recursion is guaranteed to terminate.

```bash
$ python3 polymerizationinator.py direct input.txt 15
85972
# time 800473667ns / 0.80s

$ python3 polymerizationinator.py recursive input.txt 15
85972
# time 2147194583ns / 2.15s
```

Yay! It gives me the same answer. But... it's slower. Turns out, the linked list solution is actually pretty fast and we're paying a *lot* for each recursive function call (relatively speaking).

*BUT* (and you knew there would be a but, otherwise, why would I be writing this in the first place?), we can do better:

```python
from functools import cache


def recursive(file: typer.FileText, steps: int):
    ls, map = load(file)

    # Recursively count all elements that will be returned from the character pair a,b at depth
    # This will use the mapping specified in map above
    # This will recur depth += 1 each time until depth = steps (so will always terminate)
    # The @cache will make sure that we only recalculate a given a/b/depth triple once
    @cache
    def count(a, b, depth):
        logging.info(f'{" " * depth} > count({a}, {b}, {depth})')

        ...

    ...
```

```python
$ python3 polymerizationinator.py recursive input.txt 15
85972
# time 2147194583ns / 2.15s

$ python3 polymerizationinator.py --cache recursive input.txt 15
85972
# time 43858541ns / 0.04s
```

Now *that* is what I'm talking about. 

So what in the world just happened? Well, when we're recursively building up all of these counts, we're going to run into `count(a, b, n)` more than once in the same layer. Especially as the sequence gets longer and longer, there are going to be *many* duplicates. And what's more, once you hit one of those cases, *all* of the recursive calls from that point on will be the same. What `cache` does is tell the computer to calculate a given answer (for input `a, b, depth`) *once* and store ({{< wikipedia "memoize" >}}) the answer. So we only have to do each branch once. This cuts out a *huge* amount of work. 

And... it lets us run the full 40 *really* quickly:

```bash
$ python3 polymerizationinator.py --cache recursive input.txt 40
2926813379532
# time 50570625ns / 0.05s
```

A bit less than a year, no? 

I love problems like this. Most of the time, optimization doesn't really matter. For example, if you know you're never going to run this simulation more than 10-15 generations. But every once in a while, you bump into a truly exponential function and have to run it long enough for it to explode. Then things get interesting. And that's when knowing about things like recursion and memoization come in very handy.

Cool, right?

Or right. Coming back to *that* thing. Why do we only add `b` at the end outside of the recursion? Because we're always overlapping. So when you go from `ababab` (where `ab -> c` and `ba -> d`), you're going to have recursive calls generating `acb`, `bda`, `acb`, `bda`, `acb`. Each time, the last character of one is the first of the next, so we can't count that or we'll end up overcounting. *But* that means we never do count the last `b` of the last `acb` (the only one that doesn't overlap). 

As they say, there are two hard things in computer science: caching, naming things, and off by one errors. 

Pretty sure I managed to hit all of them in this post!