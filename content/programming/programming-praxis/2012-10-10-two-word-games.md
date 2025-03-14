---
title: Two Word Games
date: 2012-10-10 14:00:09
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Word Games
---
Another day, <a title="Programming Praxis: Two Word Games" href="http://programmingpraxis.com/2012/10/09/two-word-games/">another post</a> from Programming Praxis. Today they posted a word game that seems simple enough: first find all words in a given dictionary that contain all five vowels (a, e, i, o, u) in ascending order and then find any words (at least six letters long) where the letters are all in ascending alphabetical order.

<!--more-->

First, we need some sort of framework for loading a file and looping through the lines. Luckily for us, we have the nice functions `with-input-from-file`, `with-output-to-file`, and `read-line` that will do most of the heavy lifting for us. All together, we have this:

```scheme
(define (filter-file f? fin fout)
  (with-output-to-file fout
    (lambda ()
      (with-input-from-file fin
        (lambda ()
          (let loop ([word (read-line)])
            (unless (eof-object? word)
              (let ([word (string-trim word)])
                (when (f? word)
                  (printf "~a\n" word)))
              (loop (read-line)))))))
    #:exists 'truncate))
```

This will take the input and output filenames `fin` and `fout` and a filtering function `f?`. Each line in turn will be passed to `f?`, those that return `#t` will be written to `fout`.

As a side note, the keyword argument `#:exists` tells `with-output-to-file` to overwrite the output file if it already exists. This is almost surely a Racket specific thing, but something similar probably exists in other Schemes.

Now we just need some functions to pass as `f?`.

First, a function to test if all five vowels are present and in ascending order. Basically, just filter for only the vowels, make sure that there are 5 of those and that they're all unique, and finally that they're sorted. Of course for this we need the ability to return only the unique elements in a list and test if a list is sorted, both things that I've written a dozen times before:

```scheme
(define (sorted? c? ls)
  (or (null? ls)
      (null? (cdr ls))
      (and (c? (car ls) (cadr ls))
           (sorted? c? (cdr ls)))))

(define (unique ls)
  (foldl (lambda (x l) (if (member x l) l (cons x l))) '() ls))
```

Finally, here's the function for ascending vowels:

```scheme
(define (ascending-vowels? word)
  (let ([vowels (filter
                 (lambda (c) (member c '(#\a #\e #\i #\o #\u)))
                 (string->list word))])
    (and (= (length vowels) 5)
         (= (length (unique vowels)) 5)
         (sorted? char<? vowels))))
```

Yes, `length` isn't particular efficient, but the lists really aren't going to be that long. After all, they won't be any longer than the most vowels any word has in your dictionary. After that, getting words of length at least 6 with letter in ascending order is even easier:

```scheme
(define (ascending-letters? word)
  (let ([letters (string->list word)])
    (and (>= (length letters) 6)
         (sorted? char<? letters))))
```

And that's all there is to it. I tested it on a the <a href="http://www.gnu.org/software/ispell/ispell.html" title="GNU ispell">ispell</a> dictionary and it ran in under a second, so that's good enough for me. :smile: 

Looking through some of the previous Programming Praxis <a href="http://programmingpraxis.com/contents/themes/#Word Games" title="Programming Praxis: Themes: Word Games">Word Games</a>, I think I know what I'll be doing for the next few days.

You can download the entire source for this project here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/two-word-games.rkt" title="two-word-games source">two-word-games source</a>
