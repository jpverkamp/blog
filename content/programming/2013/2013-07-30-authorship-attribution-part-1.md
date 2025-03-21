---
title: 'Authorship attribution: Part 1'
date: 2013-07-30 14:00:55
programming/languages:
- Racket
- Scheme
programming/topics:
- Computational Linguistics
- Mathematics
- Research
- Vectors
---
About two weeks ago, the new crime fiction novel <a href="http://www.amazon.com/gp/product/0316206849/ref=as_li_ss_tl?ie=UTF8&amp;camp=1789&amp;creative=390957&amp;creativeASIN=0316206849&amp;linkCode=as2&amp;tag=jverkampcom-20">Cuckoo's Calling</a> was revealed to have actually been written by J.K. Rowling under the pseudonym Robert Galbraith. What's interesting is exactly how they came to that conclusion. Here's a quote from <a title="J.K. Rowling’s Secret: A Forensic Linguist Explains How He Figured It Out" href="http://entertainment.time.com/2013/07/15/j-k-rowlings-secret-a-forensic-linguist-explains-how-he-figured-it-out/">Time</a> magazine (via <a title="J K Rowling" href="http://programmingpraxis.com/2013/07/19/j-k-rowling/">Programming Praxis</a>):

<!--more-->

> As one part of his work, Juola uses a program to pull out the hundred most frequent words across an author’s vocabulary. This step eliminates rare words, character names and plot points, leaving him with words like of and but, ranked by usage. Those words might seem inconsequential, but they leave an authorial fingerprint on any work.

> “Propositions and articles and similar little function words are actually very individual,” Juola says. “It’s actually very, very hard to change them because they’re so subconscious.”

It's actually pretty similar to what I did a few years ago for my undergraduate thesis: <a title="AnnGram" href="http://blog.jverkamp.com/category/programming/anngram/">AnnGram</a>. In that case, I used a similar technique to what they described above, [[wiki:n-grams]](), and [[wiki:Self organizing map|self organizing maps]]() to classify works by author. It's been awhile, but let's take a crack at re-implementing some of these techniques.

(If you'd like to follow along, you can see the full code here: <a href="https://github.com/jpverkamp/small-projects/tree/master/authorship">authorship attribution on github</a>)

First, we'll use the technique described above. The idea is to take the most common words throughout a book and rank them. Theoretically, this will give us a unique fingerprint for each author that should be able to identify them even under a pseudonym.

Let's start by cleaning up the words. For the time being, we want only alphabetic characters and only in lowercase. That way we should avoid position in sentences and the like. This should be an easy enough way to do that:

```scheme
; Remove non word characters
(define (fix-word word)
  (list->string 
   (for/list ([c (in-string word)] 
              #:when (char-alphabetic? c)) 
     (char-downcase c))))
```

Easy enough. So let's actually count the words. To start, we'll keep a hash of counts. They're easy enough to work with in Racket, albeit not quite so easy as say Python. With that, we only need to loop through the words in the text:

```scheme
; Store the word counts
(define counts (make-hash))

; Count all of the base words in the text
(for* ([line (in-lines in)]
       [word (in-list (string-split line))])
  (define fixed (fix-word word))
  (hash-set! counts fixed (add1 (hash-ref counts fixed 0))))
```

Using the three argument form of `hash-ref` allows us to specify a default. That way the `hash` is effectively acting like Python's `defaultdict` (a particular favorite data structure of mine). 

After we've done that, we can find the `top-n` most common words:

```scheme
; Extract the top limit words
(define top-n
  (map first
       (take
        (sort 
         (for/list ([(word count) (in-hash counts)])
           (list word count))
         (lambda (a b) (> (second a) (second b))))
        limit)))
```

Finally, we want to replace the count with the ordering. Later, we'll try using the relative frequencies but at the moment the ordering will do well enough. Since we're going to later use a default value of 0 which should be near to a low rank, we'll count down.

```scheme
; Add an order to each, descending
(for/hash ([i (in-range limit 0 -1)]
           [word (in-list top-n)])
  (values word i)))
```

All together, this can take a text file (as input port) and return the most common words. For example, using Cuckoo's Calling:

```scheme
> (with-input-from-file "Cuckoo's Calling.txt" word-rank)
'#hash(("the" . 10)  ("to" . 9)   ("and" . 8)
       ("a" . 7)     ("of" . 6)   ("he" . 5)
       ("was" . 4)   ("she" . 3)  ("in" . 2)
       ("her" . 1))
```

If the post was correct (and they did identify JK Rowling after all), then this should be a similar ordering for any book written by her while other authors will be slightly different. Let's take for example the text of the 7th Harry Potter book:

```scheme
> (with-input-from-file "Deathly Hallows.txt" word-rank)
'#hash(("the" . 10)  ("and" . 9)    ("" . 8)
       ("to" . 7)    ("of" . 6)     ("he" . 5)
       ("a" . 4)     ("harry" . 3)  ("was" . 2)
       ("it" . 1))
```

It seems that **and** has moved up, **a** and **she** have swapped, and **harry** is there--It's pretty impressive that's the 7th most common word in the entire book but rather unlikely to appear in Cuckoo's Calling. But overall, it's pretty similar. So let's try to compare it to a few more books.

We do need one more peace first though. We need to be able to tell how similar two books are. In this case, we'll use the idea of [[wiki:cosine similarity]](). Essentially, given two vectors we can calculate the angle between them. The more similar two vectors are, the closer to zero the result will be. 

One problem is that we have hashes instead of vectors. We can't even guarantee that the same words will appear in two different lists. So first, we'll unify the keys. Add zeros for missing words, put them in the same order, and we have vectors we can measure:

```scheme
; Calculate the similarity between two vectors
; If inputs are hashes, merge them before calculating similarity
(define (cosine-similarity a b)
  (cond
    [(and (hash? a) (hash? b))
     (define keys
       (set->list (set-union (list->set (hash-keys a))
                             (list->set (hash-keys b)))))
     (cosine-similarity
      (for/vector ([k (in-list keys)]) (hash-ref a k 0))
      (for/vector ([k (in-list keys)]) (hash-ref b k 0)))]
    [else
     (define cossim (acos (/ (dot-product a b) (* (magnitude a) (magnitude b)))))
     (- 1.0 (/ (abs cossim) (/ pi 2)))]))
```

The last line normalizes it to the range [0, 1.0] where the higher the number, the better match. This isn't strictly necessary, but I think it looks nicer. :smile:

Finally, we can calculate the similarity between two books. So how similar are Cuckoo's Calling and the Deathly Hallows?

```scheme
> (let ([a (with-input-from-file "Cuckoo's Calling.txt" word-rank)]
        [b (with-input-from-file "Deathly Hallows.txt" word-rank)])
    (cosine-similarity a b))
0.6965
```

About 70% (not that the numbers mean particularly much). So let's try a few more. 

Unfortunately, I don't have much in the way of crime fiction--I'm more interested in science fiction and fantasy. But that should work well enough. Using a bit of framework (<a href="https://github.com/jpverkamp/small-projects/blob/master/authorship/main.rkt">linky</a>), we can measure this easily enough. 

So, who among the author I have could have written Cuckoo's Calling? Here are the most similar books:


| 1  | 0.740 |           Butcher, Jim           |             Storm Front              |
|----|-------|----------------------------------|--------------------------------------|
| 2  | 0.739 |           Butcher, Jim           |              Side Jobs               |
| 3  | 0.738 |           Butcher, Jim           |              Turn Coat               |
| 4  | 0.736 |           Butcher, Jim           |             Small Favor              |
| 5  | 0.735 |           Butcher, Jim           |             White Night              |
| 6  | 0.734 |           Butcher, Jim           |              Cold Days               |
| 7  | 0.731 |           Butcher, Jim           |            Proven Guilty             |
| 8  | 0.729 |           Butcher, Jim           |             Ghost Story              |
| 9  | 0.728 | Stirling, S. M. & Meier, Shirley |             Shadow's Son             |
| 10 | 0.728 |          Stephen, King           |           Wizard and Glass           |
| 11 | 0.728 |         Lovegrove, James         |           The Age of Zeus            |
| 12 | 0.726 |           Butcher, Jim           |              Dead Beat               |
| 13 | 0.726 |           Duncan, Glen           |          Last Werewolf, The          |
| 14 | 0.724 |           Butcher, Jim           |              Fool Moon               |
| 15 | 0.723 |          Stephen, King           |       The Drawing of the Three       |
| 16 | 0.723 |          Adams, Douglas          | So Long, and Thanks for All the Fish |
| 17 | 0.722 |          Stephen, King           |            The Dark Tower            |
| 18 | 0.718 |         Lovegrove, James         |           The Age of Odin            |
| 19 | 0.718 |           Butcher, Jim           |               Changes                |
| 20 | 0.715 |      Chima, Cinda Williams       |           The Wizard Heir            |


Perhaps it's not surprising that Jim Butcher's books are at the top of the list. After all, it's about the closest thing that I have to crime fiction. Still, it doesn't look good that absolutely none of JK Rowling's books are in the top 20. In fact, we have to go all of the way down to 43 to find Harry Potter and the Half-Blood Prince, with a score of 0.704.

What if we average each author's books? Perhaps JK Rowling is more consistently matched against Cuckoo's Calling?

<table class="table table-striped">
<tr><td>1</td><td>0.714</td><td>Stephen, King</td></tr>
<tr><td>2</td><td>0.709</td><td>Butcher, Jim</td></tr>
<tr><td>3</td><td>0.704</td><td>Briggs, Patricia</td></tr>
<tr><td>4</td><td>0.704</td><td>Benson, Amber</td></tr>
<tr><td>5</td><td>0.698</td><td>Robinson, Kim Stanley</td></tr>
<tr><td>6</td><td>0.694</td><td>Colfer, Eoin</td></tr>
<tr><td>7</td><td>0.693</td><td>Jordan, Robert</td></tr>
<tr><td>8</td><td>0.692</td><td>Rowling, J.K.</td></tr>
<tr><td>9</td><td>0.687</td><td>Steele, Allen</td></tr>
<tr><td>10</td><td>0.687</td><td>Orwell, George</td></tr>
<tr><td>11</td><td>0.682</td><td>Croggon, Alison</td></tr>
<tr><td>12</td><td>0.681</td><td>Adams, Douglas</td></tr>
<tr><td>13</td><td>0.680</td><td>Riordan, Rick</td></tr>
<tr><td>14</td><td>0.679</td><td>Card, Orson Scott</td></tr>
<tr><td>15</td><td>0.671</td><td>Brin, David</td></tr>
<table class="table table-striped">

Not so much better, that. I have a few ideas though. Perhaps in a few days, we'll see what we can do.

If you'd like to see the full source, you can do so here: <a href="https://github.com/jpverkamp/small-projects/tree/master/authorship">authorship attribution on github</a>
