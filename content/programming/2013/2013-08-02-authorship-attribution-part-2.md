---
title: 'Authorship attribution: Part 2'
date: 2013-08-02 14:00:52
programming/languages:
- Racket
- Scheme
programming/topics:
- Computational Linguistics
- Mathematics
- Research
- Vectors
---
[Last time]({{< ref "2013-07-30-authorship-attribution-part-1.md" >}}), we used word rank to try to figure out who could possibly have written Cuckoo's calling. It didn't work out so well, but we at least have a nice framework in place. So perhaps we can try a few more ways of turning entire novels into a few numbers.

<!--more-->

Rather than word rank, how about [[wiki:stop word]]() frequency. Essentially, stop words are small words such as articles and prepositions that don't always carry much weight for a sentence's meaning. On the other hand though, those are exactly the same words that appear most commonly, so perhaps the frequencies will tell us something more.

The code is actually rather similar. To start out with, we want to load in a set of stop words. There are dozens of lists out there; any of them will work.

```scheme
; Load the stop words
(define stop-words
  (with-input-from-file "stop-words.txt"
    (lambda ()
      (for/set ([line (in-lines)]) (fix-word line)))))
```

With that, we just need to count the occurances of each word and then normalize. This will help when some books have more or less stop words overall. 

```scheme
; Calculate the relative frequencies of stop words in a text
(define (stop-word-frequency [in (current-input-port)])
  ; Store the frequency and word count
  (define counts (make-hash))
  (define total (make-parameter 0.0))

  ; Loop across the input text
  (for* ([line (in-lines in)]
         [word (in-list (string-split line))])
    (define fixed (fix-word word))

    (when (set-member? stop-words fixed)
      (total (+ (total) 1))
      (hash-set! counts word (add1 (hash-ref counts word 0)))))

  ; Normalize and return frequencies
  ; Use the order in the stop words file
  (for/vector ([word (in-set stop-words)])
    (/ (hash-ref counts word 0)
       (total))))
```

Using Cuckoo's Calling and a particular list with 50 words, we have:

```scheme
> (with-input-from-file "../target.txt" stop-word-frequency)
'#(0.043 0.003 0.000 0.002 0.026
   ...
   0.001 0.000 0.000 0.000 0.000)
```

Well that doesn't mean much to us. Hopefully it means more to the computer. :smile: 

So how similar does this one say Cuckoo's Calling and the Deathly Hallows are?

```scheme
> (let ([a (with-input-from-file "Cuckoo's Calling.txt" stop-word-frequency)]
        [b (with-input-from-file "Deathly Hallows.txt" stop-word-frequency)])
    (cosine-similarity a b))
0.877
```

That's a lot higher! Unfortunately, that doesn't really mean that they're more similar than the other test. For all we know, everything could be more similar. So let's try the entire library again:


| 1  | 0.896 |  Stephen, King  |             Wizard and Glass              |
|----|-------|-----------------|-------------------------------------------|
| 2  | 0.896 |  Rowling, J.K.  | Harry Potter and the Order of the Phoenix |
| 3  | 0.895 |  Riordan, Rick  |            The Mark of Athena             |
| 4  | 0.891 | Jordan, Robert  |              Knife of Dreams              |
| 5  | 0.891 |  Riordan, Rick  |               The Lost Hero               |
| 6  | 0.888 | Jordan, Robert  |             A Crown of Swords             |
| 7  | 0.888 |  Riordan, Rick  |            The Son of Neptune             |
| 8  | 0.887 | Croggon, Alison |                The Singing                |
| 9  | 0.887 |  Stephen, King  |         The Drawing of the Three          |
| 10 | 0.884 | Jordan, Robert  |          Crossroads of Twilight           |


Well, that's good and bad. It's unfortunate that it's not first, but we actually have a Harry Potter book in the top 10! The rest aren't that low down either, mostly appearing in the top 25. That should help with the author averages:


| 1 | 0.876 |    Jordan, Robert    |
|---|-------|----------------------|
| 2 | 0.876 |    Rowling, J.K.     |
| 3 | 0.873 |    Stephen, King     |
| 4 | 0.865 | Martin, George R. R. |
| 5 | 0.851 |    Riordan, Rick     |


None too shabby! It's a bit surprising that Robert Jordan is up at the top, but if we only consider authors that were actually around to write Cuckoo's Calling, JK Rowling is actually at the top of the list. 

Still, can we do better?

Here's another idea (that I used in my <a href="//blog.jverkamp.com"/category/programming/anngram/">previous work</a>): [[wiki:n-grams]](). Essentially, take constant sized slices of text, completely ignoring the content. So if you were dealing with the text 'THE DUCK QUACKS' and 4-grams, you would have these:

```
'THE '  'HE D'  'E DU'  ' DUC'  'DUCK'
'UCK '  'CK Q'  'K QU'  ' QUA'  'QUAC'
'UACK'
```

How does this help us? Well, in addition to keeping track of the most common words, n-grams will capture the relationships between words. Theoretically, this extra information might help out. So how do we measure it?

```scheme
; Calculate n gram frequencies
(define (n-gram-frequency [in (current-input-port)] #:n [n 4] #:limit [limit 100])

  ; Store counts and total to do frequency later
  (define counts (make-hash))

  ; Keep a circular buffer of text, read char by char
  (define n-gram (make-string 4 #\nul))
  (for ([c (in-port read-char in)])
    (set! n-gram (substring (string-append n-gram (string c)) 1))
    (hash-set! counts n-gram (add1 (hash-ref counts n-gram 0))))

  ; Find the top limit many values
  (define top-n 
    (take 
     (sort
      (for/list ([(key val) (in-hash counts)])
        (list val key))
      (lambda (a b) (> (car a) (car b))))
     limit))

  ; Cacluate the frequency of just those
  (define total (* 1.0 (for/sum ([vk (in-list top-n)]) (car vk))))
  (for/hash ([vk (in-list top-n)])
    (values (cadr vk) (/ (car vk) total))))
```

It's pretty much the same as the previous code. The only difference is the code to read the n-grams rather than the words, but that should be pretty straight forward. It's certainly not the most efficient, but it's fast enough. It can churn through a few hundred books in a few minutes. Good enough for me.

How does it perform though?


| 1  | 0.777 |     Stephen,      |   Wizard and Glass   |
|----|-------|-------------------|----------------------|
| 2  | 0.764 |  Jordan, Robert   | The Gathering Storm  |
| 3  | 0.757 | Card, Orson Scott |      Heart Fire      |
| 4  | 0.757 | Card, Orson Scott | Children of the Mind |
| 5  | 0.756 |     Stephen,      |   Song of Susannah   |
| 6  | 0.756 |     Stephen,      |    The Dark Tower    |
| 7  | 0.753 |   Butcher, Jim    |     White Night      |
| 8  | 0.751 |   Butcher, Jim    |      Turn Coat       |
| 9  | 0.746 |   Butcher, Jim    |    Captain's Fury    |
| 10 | 0.746 |   Butcher, Jim    |      Side Jobs       |


That's not so good. How about the averages?


| 1 | 0.731 |    Stephen, King,     |
|---|-------|-----------------------|
| 2 | 0.724 | Martin, George R. R.  |
| 3 | 0.715 |    Jordan, Robert     |
| 4 | 0.708 |     Butcher, Jim      |
| 5 | 0.698 | Robinson, Kim Stanley |


It turns out that JK Rowling is actually second from the bottom. Honestly, I'm not sure what this says. Did I mess up the algorithm? Well then why are Steven King, Robert Jordan, and Jim Butcher still so high up?

I still have a few more ideas though. Next week it is!
