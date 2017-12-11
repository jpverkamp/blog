---
title: NPR Sunday Puzzle
date: 2013-02-20 14:00:26
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Word Games
---
<a title="NPR Sunday Puzzle" href="https://programmingpraxis.com/2013/02/19/npr-sunday-puzzle/">Yesterday's puzzle</a> from Programming Praxis asks us to solve a Sunday Puzzle from NPR:

> Think of two familiar, unhyphenated, eight-letter words that contain the letters A, B, C, D, E and F, plus two others, in any order. What words are these?

It's another in a <a title="jverkamp.com: Word games" href="http://blog.jverkamp.com/tag/word-games/">long history of word games</a>, my favorite sort of puzzle.

<!--more-->

So how do we do it? Well, it turns out that the program is rather straight forward. You need something something that will loop through a file, reading in a line at a time. Racket's `(in-lines)` makes this all sorts of easy. So we'll start with that:

```scheme
; find all words containing _chars_ with _length_ characters
(define (words-containing chars [length (length chars)])
  (with-input-from-file DICTIONARY
    (lambda ()
      (for/list ([word (in-lines)]
                 #:when (and (= length (string-length word))
                             (andmap (lambda (c) (string-contains? word c)) chars)))
        word))))
```

It's generalized over the original problem to any required letters and any given word length. The only at all sneaky part here is using the `#:when` conditional to first check if the word is the proper length. If so, use `andmap` to make sure all of the letters are in the word in turn. The advantage of this is that `andmap` will short circuit, stopping as soon as we find a letter not in the word. It'll only save us a bit of time, but over the length of of the entire dictionary, the savings can be impressive.

Likewise, the `string-contains?` function will short circuit, using a trick with `call/cc` to simulate `return` which [I've used]({{< ref "2012-08-27-4sum.md" >}}) before:

```scheme
; test if _str_ contains the character _char_
(define (string-contains? str char)
  (call/cc 
   (lambda (return)
     (for ([c (in-string str)])
       (when (eq? c char)
         (return #t)))
     #f)))
```

And that's all there is to it. Using the same dictionary I've used before (<a title="SIL International: wordsEn.txt" href="http://www-01.sil.org/linguistics/wordlists/english/">wordsEn.txt</a>), we're ready to solve the actual problem:

```scheme
> (define DICTIONARY "wordsEn.txt")
> (words-containing (string->list "abcdef") 8)
'("boldface" "feedback")
```

And that's it. The only two common words with 8 letters, 6 of which are A through F are `boldface` and `feedback`.

If you'd like to see / download the entire code in one go, you can do so on my GitHub:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/npr-sunday-problem.rkt" title="NPR Sunday Puzzle source">NPR Sunday Puzzle source</a>