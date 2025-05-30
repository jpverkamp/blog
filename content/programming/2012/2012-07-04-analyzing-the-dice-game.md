---
title: Analyzing the dice game
date: 2012-07-04 20:47:59
programming/languages:
- Python
programming/sources:
- Lifehacker
---
Lifehacker had an <a title="How to use math and win free drinks from your friends" href="http://lifehacker.com/5923186/how-to-use-math-and-win-free-drinks-from-your-friends">interesting post</a> today where they outlined a simple dice game where you have three distinct six-sided dice, each with a different number scheme. The neat thing was that the dice had a mutually intransitive set of win probabilities, similar to rock paper scissors. So if your opponent chooses first and you choose the die that has the 5/9 edge over theirs, you will win about 5% more of the rolls (1/18). What the author claims is that this results in a 98% chance of winning over the course of 20 rolls.

A <a title="Lifehacker profile: thelongdivision" href="http://lifehacker.com/people/thelongdivision">commenter on the post</a> though, commented that the average win percentage is only 61% as opposed to the 98% mentioned in the article. I was curious if this was true, so I whipped up a quick python script to test the theory:

```python
import random

count = 1000000
rounds = 20

a_wins = 0
b_wins = 0
ties = 0

chance = 5.0 / 9.0

for i in range(count):
	a_score = 0
	b_score = 0

	for j in range(rounds):
		if random.random() < chance:
 			a_score += 1
 		else:
 			b_score += 1

	if a_score > b_score:
		a_wins += 1
	elif a_score < b_score:
		b_wins += 1
	else:
		ties += 1

print '''
a wins %.2f%%
b wins %.2f%%
%.2f%% ties
''' % (100.0 * a_wins / count,
	100.0 * b_wins / count,
	100.0 * ties / count)
```

Essentially, run 1,000,000 trials, each with the specified number of rounds. Player A will score a point 5/9 of the time, so who will win?

Well here's what running the script tells us:

```
a wins 60.92%
b wins 23.45%
15.62% ties
```

So it seems that <a title="Lifehacker profile: thelongdivision" href="http://lifehacker.com/people/thelongdivision">thelongdivision</a>'s post was completely correct. Player A (who knows the game and has the edge) has only a 61% chance of winning, rather than the 98% stated in the article--which also comes from the source article on <a title="Data Genetics -- Intransitive Dice (How to win free drinks from your friends)" href="http://www.datagenetics.com/blog/july12012/index.html">Data Genetics</a>. So what's the difference. Are they just wrong or is there some error that both the other poster and I seem to have missed?