---
title: Phone Words--In English!
date: 2021-04-09
programming/languages:
- Python
programming/topics:
- Small Scripts
programming/sources:
- LeetCode
---
Okay, let's take this one step further. Rather than generating just phone words, let's actually generate phone *words*. Someone has provided a list of words in English as a package, so we'll add a filter to add that to our comprehension:

```python
from english_words import english_words_set

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
        word
        for product in itertools.product(*[
            letters[digit] for digit in digits
        ])
        if ((word := ''.join(product)) in english_word_set)
    ]
```

I think I like the Walrus/assignment operator (`:=`), but it still is a bit bizarre at times. Basically, what it does is assign a call to a value (`word = ''.join(product)` in this case), but also returns it and can be used as an expression, which `=` cannot. So we can immediately check if it is `in english_words`. Since that's a set, it should be pretty fast. 

Let's try it:

```python
>>> letterCombinations('2665')
['amok', 'book', 'cook', 'cool']

>>> letterCombinations('43556')
['hello']

>>> letterCombinations('96753')
['world']
```

Fun! Not bad for a line more. 