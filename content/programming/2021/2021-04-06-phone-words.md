---
title: Phone Words
date: 2021-04-06
programming/languages:
- Python
programming/topics:
- Small Scripts
programming/sources:
- LeetCode
---
Working through a few problems on [LeetCode](https://leetcode.com/). I haven't quite decided what I think of the site, but it's a fun way to play with simple algorithms. Figured I might as well write up any I find interesting.

First interesting problem:

> Given a standard lettered keypad, generate all words from a given phone number.

{{< figure src="/embeds/2021/keypad.png" >}}

<!--more-->

```python
def letterCombinations(self, digits: str) -> List[str]:
    if not digits:
        return []

    letters = {
        '1': '',
        '2': 'abc',
        '3': 'def',
        '4': 'ghi',
        '5': 'jkl',
        '6': 'mno',
        '7': 'pqrs',
        '8': 'tuv',
        '9': 'wxyz',
        '0': ' ',
    }

    return [
        ''.join(product)
        for product in itertools.product(*[
            letters[digit] for digit in digits
        ])
    ]
```

I'm going to be perhaps a little overzealous when it comes to coding that. From the inside out:

* Loop over the digits with `for digit in digits`
* Get the letters for each of those with `letters[digit]`
* Generate all combinations of letters with `itertools.product` (strings are iterable)
* Join then all back together with `''.join(product)`

And that's all we need. I do love list comprehension in Python. Makes me think I'm writing in a proper language like Lisp/Scheme/Racket. :D (I should write more Racket, it's been a while). 

A few tests to make sure I'm doing something sensible:

```python
class TestSolution(unittest.TestCase):
    def test_1(self):
        self.assertEqual(
            letterCombinations("23"),
            ["ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"]
        )

    def test_2(self):
        self.assertEqual(
            letterCombinations(""),
            []
        )

    def test_3(self):
        self.assertEqual(
            letterCombinations("2"),
            ["a", "b", "c"]
        )

if __name__ == '__main__':
    unittest.main()
```

And there we go:

```bash
...
----------------------------------------------------------------------
Ran 3 tests in 0.000s

OK
```