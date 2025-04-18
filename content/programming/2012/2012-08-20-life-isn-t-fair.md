---
title: Life isn't fair...
date: 2012-08-20 14:00:19
programming/languages:
- Python
---
...but if you have an unfair coin, you can fix it!

Based on <a title="Laur­en Ipsum and the Un­fair Coin" href="http://carlos.bueno.org/2011/10/fair-coin.html">this post over at Lauren Ipsum</a>, you can use statistics to make any unfair coin (defined as something that can return either heads or tails with some arbitrary but constant percent chance) into a fair one with a 50/50 chance of heads or tails.

<!--more-->

If you look at it, it's easy enough to make sense of the math. If you have a coin with a 70% chance of flipping heads, for example, you have the following outcomes when you flip the coin twice:

| Heads, Heads | 49% |
|--------------|-----|
| Heads, Tails | 21% |
| Tails, Heads | 21% |
| Tails, Tails | 9%  |

The neat bit is that it's equally likely to get either heads than tails or tails than heads. So all you have to do is flip the coin over and over in pairs until you get a pair where the two results are different, then return the first of the pair. Voila, instant fair coin.

Here's a nice Python script demonstrating the idea:

```python
import random

class Coin(object):
	def __init__(self, r):
		self.r = r
		self.f = 0

	def flip(self):
		self.f += 1
		return random.random() < self.r

if __name__ == '__main__':
	for tries in xrange(5):
		r = random.random()
		print 'Generating a coin with r = %s' % r

		c = Coin(r)

		h = 0
		t = 0
		for i in xrange(10000):
			while True:
				a = c.flip()
				b = c.flip()

				if a != b:
					if a:
						h += 1
					else:
						t += 1
					break

		print '''
=== Results ===
heads: %d (%.2f%%)
tails: %d (%.2f%%)
flips: %d
''' % (h, 100.0 * h / (h + t), t, 100.0 * t / (h + t), c.f)
```

If you run it a few time, here's the output:

```
=== Results ===
heads: 5051 (50.51%)
tails: 4949 (49.49%)
flips: 53850

Generating a coin with r = 0.0305335132684

=== Results ===
heads: 5038 (50.38%)
tails: 4962 (49.62%)
flips: 344130

Generating a coin with r = 0.953169761122

=== Results ===
heads: 5047 (50.47%)
tails: 4953 (49.53%)
flips: 224368

Generating a coin with r = 0.186813443725

=== Results ===
heads: 5078 (50.78%)
tails: 4922 (49.22%)
flips: 65848

Generating a coin with r = 0.717615022909

=== Results ===
heads: 5023 (50.23%)
tails: 4977 (49.77%)
flips: 49392
```

As you can see, no matter how unfair the original coin, the result is always within 1% of being perfectly even. Well within statistical variation.

Sometimes, math is awesome.

If you'd like to download the source code, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/life-isnt-fair.py" title="Life Isn't Fair source">Life Isn't Fair source</a>