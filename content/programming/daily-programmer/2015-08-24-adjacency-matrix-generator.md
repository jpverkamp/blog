---
title: Adjacency Matrix Generator
date: 2015-08-24
programming/languages:
- Python
programming/sources:
- Daily Programmer
programming/topics:
- Graphs
---
Been a while since I've actually tackled one of the [Daily Programmer](/programming/sources/daily-programmer/) challenges, so let's try one out. From <a href="https://www.reddit.com/r/dailyprogrammer/comments/3h0uki/20150814_challenge_227_hard_adjacency_matrix/)">a week and a half ago</a>, we are challeneged to make an adjacency matrix generator, turning a graphical representation of a graph into an [[wiki:adjacency matrix]]().

Input:

```text
a-----b
|\   / \
| \ /   \
|  /     e
| / \   /
|/   \ /
c-----d
```

Output:

```text
01110
10101
11010
10101
01010
```

<!--more-->

Specifically, we're working under a few conditions:


* Nodes[^1] will be represented by a lowercase letter `a` to `z` (there will never be more than 26 nodes)
* Edges are either horizontally, vertically, or diagonally at 45 degrees and will be represented by `|-/\\`
* All edges will have a node at each end
* Any two nodes have at most one edge between them
* If edges need to bend, a virtual node marked by a `#` will be inserted (see examples later)
* Edges can overlap; there will always be at least one directed edge adjacent to each node


My general idea for a solution takes place in three parts:


* Load the grid into a quickly accessible form
* From each node, try each of the 8 cardinal directions looking for an edge; on an edge follow it until you hit either: 
* Another node: record the edge
* A virtual node: recursively check that edge instead
* Print out the edges found above


Let's do it. First, read in the edges:

```python
from collections import defaultdict as ddict

# Points will be stored as (row, col) tuples
# The grid is a mapping of points to the character in that location
# Nodes nodes store their point for fast iteration
# The final solution will be a mapping of nodes to a set of other nodes adjacent to them
grid = ddict(lambda : ' ')
nodes = {}
adjacency = ddict(set)

# Read the rest of the grid
for row, line in enumerate(sys.stdin):
    for col, char in enumerate(line):

        pt = (row, col)
        grid[pt] = char

        if is_node(char):
            nodes[char] = (row, col)
```

Straight forward. I love `defaultdict`, since it means we don't have to worry about looking for points off the edge of the grid. If it's out of bounds, it will just return empty space.

Next, the 'seeking' function, that will follow an edge until a node (either real or virtual):

```python
# List of possible edges, ordered row, col, edge type
possible_edges = (
    (-1, -1, '\\'), (-1, 0, '|'), (-1, 1, '/'),
    ( 0, -1, '-'),                ( 0, 1, '-'),
    ( 1, -1, '/'),  ( 1, 0, '|'), ( 1, 1, '\\')
)

def neighbors(src_pt, previous_deltas = None):
    '''Given a point, yield any neighboring nodes'''

    src = grid[src_pt]
    row, col = src_pt

    for row_delta, col_delta, edge_type in possible_edges:

        dst_pt = (row + row_delta, col + col_delta)
        dst = grid[dst_pt]

        # Don't go back the way we came
        if (-row_delta, -col_delta) == previous_deltas:
            continue

        # A valid leaving edge, follow it until a node or a #
        elif dst == edge_type:
            for i in naturals(2):
                dst_pt = (row + i * row_delta, col + i * col_delta)
                dst = grid[dst_pt]

                # Found the target node, add
                if is_node(dst):
                    yield dst
                    break

                # Found a connector, continue on the other exit point
                elif dst == '#':
                    yield from neighbors(dst_pt, (row_delta, col_delta))
                    break
```

Basically, we have eight `possible_edges`, each of which has a delta along the row and column, along with the character that has to start and end it (the rest could be under something else, we don't really care, since we're making the assumption that the input is well formed).

I did use a couple of helper functions here. They should be fairly obvious:

```python
def is_node(c):
    return c in 'abcdefghijklmnopqrstuvwxyz'

def is_edge(c):
    return c in '|-/\\'

def naturals(i = 0):
    while True:
        yield i
            i += 1
```

That includes one trick I've picked up from my [Racket]({{< ref "2014-06-11-call-stack-bracket-matcher.md" >}}) posts. `naturals` is an infinite list (a generator) of all natural numbers, starting at the given point. It's useful in this case since we don't know how far we're going to run along the edge, just that it will end eventually.

Finally, we need functions to iterate over all of the nodes as starting points and then to print out the results:

```python
# Start at each node and expand all edges
# Note: This will find each edge twice, so it goes
for (src, pt) in nodes.items():
    for dst in neighbors(pt):
        adjacency[src].add(dst)
        adjacency[dst].add(src)

# Print an adjacency matrix in sorted node order
for src in sorted(nodes):
    for dst in sorted(nodes):
        if dst in adjacency[src]:
            sys.stdout.write('1')
        else:
            sys.stdout.write('0')
    sys.stdout.write('\n')
```

As noted, this will find each edge twice, but so it goes. To account for that, we would have to use up a bit more memory storing the state of where we've been. As it is, we have a mostly functional solution, which I like.

And that's it. Let's see a few of the test cases from the <a href="https://www.reddit.com/r/dailyprogrammer/comments/3h0uki/20150814_challenge_227_hard_adjacency_matrix/)">original post</a>:

```bash
$ cat 1.matrix; python3 matrix-reader.py < 1.matrix

7
a-----b
|\   / \
| \ /   \
|  /     e
| / \   /
|/   \ /
c-----d

01110
10101
11010
10101
01010

$ cat 3.matrix; python3 matrix-reader.py < 3.matrix

7
a  b--c
|    /
|   /
d  e--f
 \    |
  \   |
g--h--#

00010000
00100000
01001000
10000001
00100100
00001001
00000001
00010110

9
   #--#
   | /        #
   |a--------/-\-#
  #--\-c----d   /
   \  \|     \ / \
   |\  b      #   #
   | #  \        /
   |/    #------#
   #

0111
1011
1101
1110
```

Shiny!

I wonder how hard it would be to program the inverse: take an adjacency matrix as input and generate one of these graphical matrices as output? Even better, generate an 'optimal' graphic, with the smallest possible area.

We'll see.

The full code is available on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/matrix-reader.py">matrix-reader.py</a>

[^1]: I never remember how to spell vertices