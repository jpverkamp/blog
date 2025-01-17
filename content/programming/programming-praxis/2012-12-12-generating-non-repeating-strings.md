---
title: Generating non-repeating strings
date: 2012-12-12 14:00:32
programming/languages:
- Python
- Racket
- Scheme
programming/sources:
- Programming Praxis
---
Based on <a title="Programming Praxis: Stepwise Program Development: A Heuristic Algorithm" href="http://programmingpraxis.com/2012/12/11/stepwise-program-development-a-heuristic-algorithm/">this post</a> from Programming Praxis, today's goal is to write an algorithm that, given a number *N* and an alphabet *A*, will generate all strings of length N made of letters from A with no adjacent substrings that repeat.

So for example, given *N = 5* and *A = {a, b, c}* the string *abcba* will be allowed, but none of *abcbc*, *ababc*, nor even *aabcb* will be allowed (the *bc*, *ab*, and *a* repeat).

It's a little more general even than the version Programming Praxis specifies (they limit the alphabet to exactly *A = {1, 2, 3} *and more more general still than their original source which requires only one possible string, but I think it's worth the extra complications.

<!--more-->

To start out with, let's just brute force the problem. Generate all possible sequences of characters in turn. For each, loop over every possible splitting point and every possible length at that splitting point. If any of those result in a duplicate substring, throw it out. We're doing more work than we have to, generating strings where we can already tell after just the first two characters that they repeat, but that's for future optimizations, yes?

So we'll start with code that given a length and an alphabet will give us all possible strings. This is a perfect use of recursion and generators (in the Python version).

Python:
```python
def combinations(N, A):
	'''Generate all strings from A of length N.'''
	if N == 0:
		yield ''
	else:
		for c in A:
			for s in combinations(N - 1, A):
				yield c + s
```

Racket:
```scheme
; generate all strings from A of length N
(define (combinations n a)
  (map list->string
       (let loop ([n n])
         (cond
           [(zero? n) '(())]
           [else
            (for*/list ([c (in-string a)]
                        [r (in-list (loop (- n 1)))])
              (cons c r))]))))
```

In the case of Racket, I nest the helper *loop* just so that I can map *list->string* at the end. If I were just looking for lists or if I had used *string-append* rather than *cons* that wouldn't have been necessary.

Next, we want a function that can check if there are any duplicate substrings. As aforementioned, we'll generate each index in the string (ignoring the very first and last) and check each length substring before and after that index.

Python:
```python
def has_repeat(s):
	'''Check if a string has a non-empty repeating substring.'''

	N = len(s)
	for i in xrange(1, N):
		for j in xrange(1, min(i, N - i) + 1):
			if s[i-j:i] == s[i:i+j]:
				return True

	return False
```

Racket:
```scheme
; check if a string has a non-empty repeating substring
(define (repeats? s)
  (call/cc
   (lambda (return)
     (define N (string-length s))
     (for* ([i (in-range 1 N)]
            [j (in-range 1 (+ 1 (min i (- N i))))])
       (when (equal? (substring s (- i j) i)
                     (substring s i (+ i j)))
         (return #t)))
     (return #f))))
```

Using *call/cc* like this is a trick to bail out of the loop early. Otherwise, we could have used *andmap*, but I much prefer being able to use *for**.

And now that the hard part is out of the way, we can put it all together:

Python:
```python
def non_repeating_direct(N, A):
	'''
	Generate all strings of length N from the alphabet A
	such that no adjacent substrings are repeated.
	'''

	return [s for s in combinations(N, A) if not has_repeat(s)]
```

Racket:
```scheme
; generate all strings of length N from alphabet A with no repeating substrings
(define (non-repeating-direct N A)
  (for/list ([s (in-list (combinations N A))]
             #:when (not (repeats? s)))
    s))
```

So how does it work out?

```scheme
> (time (non-repeating-direct 5 "abc"))
cpu time: 0 real time: 2 gc time: 0
'("abaca" "abacb" "abcab" "abcac" "abcba"
  "acaba" "acabc" "acbab" "acbac" "acbca"
  "babca" "babcb" "bacab" "bacba" "bacbc"
  "bcaba" "bcabc" "bcacb" "bcbab" "bcbac"
  "cabac" "cabca" "cabcb" "cacba" "cacbc"
  "cbabc" "cbaca" "cbacb" "cbcab" "cbcac"))
```

Looks good so far.

As an interesting aside, <a href="http://gravatar.com/benmmurphy">Ben</a> over in the Programming Praxis comments pointed out that the number of such words corresponds with the number of <a href="http://oeis.org/A006156" title="OEIS Sequence number A006156">ternary squarefree words of length n</a>:
```scheme
> (for/list ([n (in-range 10)]) (length (non-repeating-direct n "abc")))
'(1 3 6 12 18 30 42 60 78 108)
```

And actually once you parse through all of the jargon, it makes perfect sense. [[wiki:Ternary]]() is base three (thus the alphabet *A = {a, b, c}*), words are what we are generating of length *n*, and a [[wiki:squarefree word]]() is one without any adjacent subwords.

The full source code (along with unit tests) is available here:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/non-repeating-strings.py" title="Python non-repeating strings source on GitHub">Python source</a>
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/non-repeating-strings.rkt" title="Racket non-repeating strings source on GitHub">Racket source</a>
