---
title: "AoC 2018 Day 2: Counting letters"
date: 2018-12-02
programming/languages:
- Python
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [Inventory Management System](https://adventofcode.com/2018/day/2)

> **Part 1:** Given a list of strings, count how many contain exactly two of a letter (`a`) and how many contain exactly three of a letter (`b`). Calculate `a*b`.

<!--more-->

Bit weirdly stated. My first thought would be to use {{< wikipedia "regular expressions" >}}[^regexhammer], but that doesn't actually fit supper well with this case, because you need _exactly_ two matches. I'm not actually sure how you'd even write something like that, since you'd have to match against 'not this' _before you found the first match_. Meh.

In both Racket and Python, I'm going to create a hash that maps each unique letter in a word to how many times that letter occurs:

```racket
(define (count-letters word)
  (for/fold ([count (hash)])
            ([letter (in-string word)])
    (hash-update count
                 letter
                 add1
                 0)))
```

```python
def count_letters(word):
    counts = collections.defaultdict(lambda : 0)
    for letter in word.strip():
        counts[letter] += 1
    return counts
```

If you have that, you can count the letters and look in those hash values (we don't actually care about keys here) for 2s and 3s:

```racket
(define-values (2s 3s)
  (for/fold ([2s 0] [3s 0])
            ([line (in-lines)])
    (define counts (count-letters (string-trim line)))
    (values (+ 2s (if (member 2 (hash-values counts)) 1 0))
            (+ 3s (if (member 3 (hash-values counts)) 1 0)))))

(* 2s 3s)
```

```python
count_2s = 0
count_3s = 0

for word in fileinput.input():
    counts = count_letters(word)
    if 2 in counts.values(): count_2s += 1
    if 3 in counts.values(): count_3s += 1

print(count_2s * count_3s)
```

In this case, the code is pretty much the same in both the Racket and the Python case. The Racket case is half function in that we're using {{< doc racket "for/fold" >}} to update an immutable hash, but because this is Racket (and we have the whole {{< doc racket for >}} family), it looks much the same as Python's more iterative version.

If you wanted a slightly more 'traditional' Scheme version, you could do something like this:

```racket
(let loop ([2s 0] [3s 0] [lines (port->lines)])
  (cond
    [(empty? lines) (* 2s 3s)]
    [else
     (define counts (count-letters (string-trim (first lines))))
     (loop (+ 2s (if (member 2 (hash-values counts)) 1 0))
           (+ 3s (if (member 3 (hash-values counts)) 1 0))
           (rest lines))]))
```

To each their own.

They all return the same value though:

```bash
$ cat input.txt | racket counting-letters.rkt

4980

$ cat input.txt | racket counting-letters-functional.rkt

4980

$ cat input.txt | python3 counting-letters.py

4980
```

> **Part 2:** Given the same list of words, find the two words with exactly one letter different. Print all letters that were the same.

Not really much code you can re-use. For this, you really want a function that can count differences and another to show what is the same (you only actually need the second, but :shrug:):

```racket
(define (differences word1 word2)
  (for/sum ([letter1 (in-string word1)]
            [letter2 (in-string word2)]
            #:unless (char=? letter1 letter2))
    1))

(define (shared-letters word1 word2)
  (list->string
   (for/list ([letter1 (in-string word1)]
              [letter2 (in-string word2)]
              #:when (char=? letter1 letter2))
     letter1)))
```

The main interesting bit here is the use of the `#:when` / `#:unless` clauses in the loops to only evaluate the body if / not if a condition is matched. An `if` in the body of the `for` would work much the same way in this case.

With that, we can use {{< doc racket "for*/first" >}} to find the first word with exactly one difference (since the puzzle spec says there will only be one) and then {{< doc racket apply >}} the `shared_letters` function to it:

```racket
(define words (port->lines))

(apply shared-letters
       (for*/first ([word1 (in-list words)]
                    [word2 (in-list words)]
                    #:when (= 1 (differences word1 word2)))
         (list word1 word2)))
```

And once again, I'm going to basically translate directly into Python:

```python3
def differences(word1, word2):
    count = 0
    for letter1, letter2 in zip(word1, word2):
        if letter1 != letter2:
            count += 1
    return count

def shared_letters(word1, word2):
    output = []
    for letter1, letter2 in zip(word1, word2):
        if letter1 == letter2:
            output.append(letter1)
    return ''.join(output)

words = list(fileinput.input())

for word1 in words:
    for word2 in words:
        if differences(word1, word2) == 1:
            print(shared_letters(word1, word2))
            exit()
```

Bit ugly to have that `exit` in the loop there. Sometimes I miss being able to jump out of multiple loops without leaving a function entirely (with `return`) in Python[^missingphp].

```bash
$ cat input.txt | racket near-misses.rkt

"qysdtrkloagnfozuwujmhrbvx"

$ cat input.txt | python3 near-misses.py

qysdtrkloagnfozuwujmhrbvx
```

Slight differences in output since I'm relying on Racket's behavior of printing out top level values for each expression rather than explicitly printing things. So it goes.

[^regexhammer]: When you have a hammer...
[^missingphp]: Who would have thought.
