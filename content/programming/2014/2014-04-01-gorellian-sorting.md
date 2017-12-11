---
title: Gorellian sorting
date: 2014-04-01 14:00:09
programming/languages:
- Python
- Racket
- Scheme
---
It's been a while, so I figured I should get in a quick coding post. From /r/dailyprogrammer, we have <a href="http://www.reddit.com/r/dailyprogrammer/comments/20sjif/4192014_challenge_154_intermediate_gorellian/">this challenge</a>:

> The Gorellians, at the far end of our galaxy, have discovered various samples of English text from our electronic transmissions, but they did not find the order of our alphabet. Being a very organized and orderly species, they want to have a way of ordering words, even in the strange symbols of English. Hence they must determine their own order.

> For instance, if they agree on the alphabetical order:
> UVWXYZNOPQRSTHIJKLMABCDEFG

> Then the following words would be in sorted order based on the above alphabet order:
> WHATEVER
> ZONE
> HOW
> HOWEVER
> HILL
> ANY
> ANTLER
> COW

<!--more-->

To a large extent, this problem is made all the easier by the choice of host language. If I were writing in something like Python, it's easy enough to sort a list:

```python
words = sorted(['ANTLER', 'ANY', 'COW', 'HILL', 'HOW', 'HOWEVER', 'WHATEVER', 'ZONE'])
```

But it's a little more complicated to sort in a non-standard order. Essentially--you can't. Instead, you have to specify a `key` function in order to convert each value from what you have to something you can sort. Something like this:

```python
def make_gorellian(alphabet):
	def to_offset_list(string):
		return [alphabet.index(c) for c in string]
	return to_offset_list
```

Perhaps I've been writing too much Scheme recently. :smile: Still, I hope it's clear enough. We have a function `make_gorellian` which constructs and returns a second function `to_offset_list`. This inner function takes any string and converts into a list of numbers--something Python knows how to sort. 

For example:

```python
>>> print list(sorted(
	['ANTLER', 'ANY', 'COW', 'HILL', 'HOW', 'HOWEVER', 'WHATEVER', 'ZONE'],
	key = make_gorellian('UVWXYZNOPQRSTHIJKLMABCDEFG')
))
['WHATEVER', 'ZONE', 'HOW', 'HOWEVER', 'HILL', 'ANY', 'ANTLER', 'COW']
```

There you go. Straight forward enough, although it seems odd that we have to go through an intermediary form. 

So what was that I said about more natural mappings? Well, in Scheme/Racket, `sort` takes two arguments: a list to sort and a 'less than' function. If you wanted to sort strings, you could call something like this:

```scheme
(sort ls string<?)
```

So all we need is `gorellian&lt;?`. Well, how does `string&lt;?` normally work? By repeatedly calling `char&lt;?`. So we need a `gorellian-char&lt;?`. Something like this:

```scheme
; Sort characters by a non-standard alphabet
(define (make-gorellian-char<? alphabet)
  (λ (c1 c2)
    ; If we match either, we have an answer
    ; If we never match, they're = (and thus not <)
    (for/first ([c (in-string alphabet)]
                #:when (or (eq? c c1) (eq? c c2)))
      ; If we matched c1 first, the c1 is smaller
      (eq? c c1))))

; Sort strings by a non-standard alphabet
(define (make-gorellian-string<? alphabet)
  (define char<? (make-gorellian-char<? alphabet))
  (λ (str1 str2)
    (for/first ([c1 (in-string str1)]
                [c2 (in-string str2)]
                #:unless (eq? c1 c2))
      (char<? c1 c2))))
```

It's interesting how similar the two functions are. In the first, we loop through the alphabet until we find either character. If we find the first first, it's 'less than'. If we find the second first or find neither, then `c1` is not less than `c2`. So return `#f`.

For the `string&lt;?`, it's more of the same. Loop through the strings until we find a mismatch, at which point we can use the `char&lt;?` function.

And that's all we have for it. A few test cases:

```scheme
(module+ test
  (require rackunit)

  ; Run test cases in the format specified here:
  ; http://www.reddit.com/r/dailyprogrammer/comments/20sjif/4192014_challenge_154_intermediate_gorellian/
  (define (test [in (current-input-port)])
    (define sample-count (read in))
    (define alphabet (symbol->string (read in)))
    (define string<? (make-gorellian-string<? alphabet))
    (define words
      (for/list ([i (in-range sample-count)])
        (symbol->string (read in))))
    (sort words string<?))

  (check-equal? 
   (call-with-input-string 
    "
8 UVWXYZNOPQRSTHIJKLMABCDEFG
ANTLER
ANY
COW
HILL
HOW
HOWEVER
WHATEVER
ZONE
"
   test)
   '("WHATEVER" "ZONE" "HOW" "HOWEVER" "HILL" "ANY" "ANTLER" "COW"))

  (check-equal?
   (call-with-input-string 
    "
5 zZyYxXwWvVuUtTsSrRqQpPoOnNmMlLkKjJiIhHgGfFeEdDcCbBaA
go
aLL
ACM
teamS
Go
"
    test)
   '("teamS" "go" "Go" "aLL" "ACM")))
```

And that's all she wrote.

(For the keen of eye, I am changing the definition slightly. Rather than an error on missing letters, I treat all non-Gorellian letters as equal. Still, it would be easy enough to add. 

Code:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/gorellian-sort.py">python</a>
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/gorellian-sort.rkt">racket</a>

<small>Nope. Nothing for April Fools'. Maybe you should go <a href=http://googleasiapacific.blogspot.com/2014/03/become-pokemon-master-with-google-maps.html">catch some Pokemon</a>.</small>
