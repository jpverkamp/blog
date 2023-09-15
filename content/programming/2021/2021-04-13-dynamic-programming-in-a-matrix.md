---
title: Dynamic Programming over a Matrix
date: 2021-04-13
programming/languages:
- Python
programming/topics:
- Small Scripts
programming/sources:
- LeetCode
---
Another LeetCode problem.

> Given an `MxN` matrix of numbers, find the longest path of strictly increasing numbers. 

So for example in this matrix:

<table>
<tr><td>9</td><td>9</td><td>4</td></tr>
<tr><td>6</td><td>6</td><td>8</td></tr>
<tr><td>2</td><td>1</td><td>1</td></tr>
</table>

You can start with the 1 in the bottom center, go left to the two, then up to the 6, and 9. That's the longest path, so return a 4. 

In this 3x3 case, it's really easy to just brute force. Calculate all possible paths. An upper bound would be visiting every node exactly once, so {{< inline-latex "\sum_{i=1}^9 \binom{9}{i} = 511" >}} (choose `n` elements for each of 1 to 9 cases). Not so bad. But if you have a 10x10 matrix, that's already 1e30--which is freaking gigantic. So we need to do better.

Luckily, it's actually pretty easy to do better! Just use [[wiki:dynamic programming]]() and/or [[wiki:memoization]]()! Basically, create a second matrix the same side as the first where eventually every value will be the size of the longest path *from that element*. Assume that you can build that. Then to actually calculate any specific value, you can look at the 4 surrounding values in both sets of data. For any neighboring values that are less, find their chain length, then add one to the largest. 

Let's work an example. Start in the top left of the matrix above. With the 9, the only possible chain would be to go downward, so

```text
f(top left) = f(center left) + 1
```

From there, we can only go down again.

```text
f(center left) = f(bottom left) + 1
```

Continue on and you can only go to the bottom center:

```text
f(bottom left) = f(bottom center) + 1
```

And at that point, we have to stop since there's no where to go. Fill it the recursion:

```text
f(bottom center) = 1
f(bottom left) = f(bottom center) + 1 = 2
f(center left) = f(bottom left) + 1 = 3
f(top left) = f(center left) + 1 = 4
```

<table>
<tr><td>4</td><td>*</td><td>*</td></tr>
<tr><td>3</td><td>*</td><td>*</td></tr>
<tr><td>2</td><td>1</td><td>*</td></tr>
</table>

Now we can move on to the top center. That one can go either right (to the 4) or down (to the 6):

```text
f(top center) = max(f(top right), f(center center)) + 1
```

Top right is already a minimum, because none of them are less than 4.

```text
f(top right) = 1
```

But the center can go down. We already know that value though! (it was 1)

```text
f(center center) = f(bottom center) + 1
```

Calculate everything:

```text
f(center center) = f(bottom center) + 1 = 2
f(top center) = max(f(top right), f(center center)) + 1
f(top center) = max(1, 2) + 1 
f(top center) = 2 + 1
f(top center) = 3
```

So now we have:

<table>
<tr><td>4</td><td>3</td><td>1</td></tr>
<tr><td>3</td><td>2</td><td>*</td></tr>
<tr><td>2</td><td>1</td><td>*</td></tr>
</table>

We already have the next two, so skip to the center right! (see, with a bit of extra memory). It can go any of three directions:

```text
f(center right) = max(f(top right), f(center center), f(bottom right)) + 1
```

We know the first two, but need the bottom right. That's a 1 (minimum), so is just 1.

Fill it back in!

```text
f(center right) = max(f(top right), f(center center), f(bottom right)) + 1
f(center right) = max(1, 2, 1) + 1
f(center right) = 2 + 1
f(center right) = 3
```

<table>
<tr><td>4</td><td>3</td><td>1</td></tr>
<tr><td>3</td><td>2</td><td>*</td></tr>
<tr><td>2</td><td>1</td><td>*</td></tr>
</table>

And we're done. The maximum value of this second table is `4`, so we're done. That's the answer. And rather than checking all 1e30 possible answers, we only have to check each cell at most once. So `100` iterations. Much much much faster!

To turn that to code, we can cheat a bit. There's a function in the standard library: {{< doc python "functools.cache" >}}. If you apply that to a function, it will automatically [[wiki:memoize]]() it. The first time the function runs, it will do the normal thing, but when returning, it will store the answer in a Dict of type `Dict[input type, output type]`. In this case, `Dict[(int, int), int]`. The next time (and every time afterwards), just look up and return this cached value. Much quicker!

Code:

```python
def longestIncreasingPath(self, matrix: List[List[int]]) -> int:
    if not matrix or matrix == [[]]:
        return 0

    width = len(matrix)
    height = len(matrix[0])

    @cache
    def f(x, y):
        return max([1] + [
            f(xi, yi) + 1
            for xi, yi in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            if (
                xi >= 0 and xi < width
                and yi >= 0 and yi < height
                and matrix[xi][yi] < matrix[x][y]
            )
        ])

    return max(
        f(x, y)
        for x in range(width)
        for y in range(height)
    )
```

That's it! Within the function, we iterate over the possible next values (`xi` and `yi`). If they're still on the matrix and the value is less than the current, include them in the generator. Apply `max` to that (and put `[1]` in there as a base value, because you can always have a chain by itself) and that will calculate the entire second matrix. Apply a `max` over that and we're done!

Tests:

```python
class TestSolution(unittest.TestCase):
    def test_1(self):
        self.assertEqual(4, longestIncreasingPath([[9,9,4],[6,6,8],[2,1,1]]))

    def test_2(self):
        self.assertEqual(4, longestIncreasingPath([[3,4,5],[3,2,6],[2,2,1]]))

if __name__ == '__main__':
    unittest.main()
```

Run it:

```bash
..
----------------------------------------------------------------------
Ran 2 tests in 0.000s

OK
```

Fun! 

And you can run the giant things as well:

```python
>>> matrix = [[random.randint(1, 1000000) for i in range(100)] for j in range(100)]

>>> start = time.time(); print(Solution().longestIncreasingPath(matrix)); end = time.time()
14

>>> print(end - start)
0.03310894966125488
```

Fun! :D