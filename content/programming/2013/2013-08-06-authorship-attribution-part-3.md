---
title: 'Authorship attribution: Part 3'
date: 2013-08-06 14:00:53
programming/languages:
- Racket
- Scheme
programming/topics:
- Computational Linguistics
- Mathematics
- Research
- Vectors
---
So far, we've had three different ideas for figuring out the author of an unknown paper (top n word ordering in [Part 1]({{< ref "2013-07-30-authorship-attribution-part-1.md" >}}) and stop word frequency / 4-grams in [Part 2]({{< ref "2013-08-02-authorship-attribution-part-2.md" >}})). Here's something interesting though from the comments on the <a title="JK Rowling" href="http://programmingpraxis.com/2013/07/19/j-k-rowling/">Programming Praxis post</a>:

> <cite>Globules</cite> said
> <small>July 19, 2013 at 12:29 PM</small>
> Patrick Juola has a <a href="http://languagelog.ldc.upenn.edu/nll/?p=5315" rel="nofollow">guest post on Language Log</a> describing the approach he took.

<!--more-->

If you read through this though, there are some interesting points. Essentially, the worked with only a single known novel from JK Rowling (which I don't have): <a href="http://www.amazon.com/gp/product/0316228583/ref=as_li_ss_tl?ie=UTF8&amp;camp=1789&amp;creative=390957&amp;creativeASIN=0316228583&amp;linkCode=as2&amp;tag=jverkampcom-20&quot;>The Casual Vacancy</a><img src=&quot;http://ir-na.amazon-adsystem.com/e/ir?t=jverkampcom-20&amp;l=as2&amp;o=1&amp;a=0316228583">The Casual Vacancy</a>. Theoretically that will help, since it's more likely to be similar in style than the Harry Potter books; although that seems to defeat the idea of an author having a universal writing style. Other than that though, they analyzed three other Brittish crime authors. So the works they used are completely different.

Another change is that, rather than analyzing the entire document as a whole, they broken each text into 1000 word chunks. This should theoretically help with outliers and somewhat offset the fact that there is a significantly smaller library. On the other hand though, as the author talks about more and more features, I can't help but feel that they choose features specifically to out JK Rowling as the author... In their results, they have a 6/5 split favoring JK Rowling for one test, a 4/4/3 favoring her for another, and a 8/3 against JK Rowling in the third. So it's still not a particularly solid conclusion...

In any case, I still do have one more test to run based on their article (if you're read the <a title="authorship attribution source code" href="https://github.com/jpverkamp/small-projects/tree/master/authorship">source on GitHub</a> you've probably already seen this): word length. That's actually the most successful of their tests, with the 6/5 split, so theoretically it might work out better?

At this point, the code is almost trivial to write. Basically, we'll take the [previous top n word code]({{< ref "2013-07-30-authorship-attribution-part-1.md" >}}) and cut out most of it:

```scheme
; Calculate the relative frequencies of stop words in a text
(define (word-lengths [in (current-input-port)])
  ; Store the length counts
  (define counts (make-hash))

  ; Count all of the base words in the text
  (for* ([line (in-lines in)]
         [word (in-list (string-split line))])
    (define len (string-length word))
    (hash-set! counts len (add1 (hash-ref counts len 0))))

  counts)
```

And that's all there is to it. Yes, it does treat punctuation as part of word length. That's perfectly expected (if not entirely optimal). Let's see it in action:

```scheme
> (define cc-hash (with-input-from-file "Cuckoo's Calling.txt" word-lengths))
> (for/list ([i (in-range 1 10)])
    (hash-ref cc-hash i 0))
'(0.031 0.134 0.222 0.173 0.122 0.103 0.083 0.053 0.033)

> (define dh-lengths (with-input-from-file "Deathly Hallows.txt" word-lengths))
> (for/list ([i (in-range 1 10)])
    (hash-ref dh-lengths i 0))
'(0.045 0.138 0.211 0.174 0.128 0.100 0.078 0.051 0.034)
```

To the naked eye, those look pretty dang similar. In fact, they are:

```scheme
> (cosine-similarity cc-hash dh-hash)
0.964
```

That looks good, but does it work overall? Here are the by-book results:


| 1  | 0.979 |  Jordan, Robert  |  The Path of Daggers   |
|----|-------|------------------|------------------------|
| 2  | 0.975 |  Jordan, Robert  |    Knife of Dreams     |
| 3  | 0.973 |  Jordan, Robert  | Crossroads of Twilight |
| 4  | 0.972 | Croggon, Alison  |        The Gift        |
| 5  | 0.971 | Pratchett, Terry |      Equal Rites       |
| 6  | 0.970 |   Butcher, Jim   |   Furies of Calderon   |
| 7  | 0.970 |  Jordan, Robert  |   A Crown of Swords    |
| 8  | 0.969 |  Jordan, Robert  |     Winter's Heart     |
| 9  | 0.968 |  Jordan, Robert  |  The Gathering Storm   |
| 10 | 0.967 |  Jordan, Robert  |   A Memory of Light    |


Not so good... It turns out that these numbers are similar across pretty much all English language texts. The lowest score for any book I have is still 0.902. Perhaps the by-author results will do better:


| 1 | 0.964 |    Jordan, Robert     |
|---|-------|-----------------------|
| 2 | 0.964 |    Croggon, Alison    |
| 3 | 0.959 | Robinson, Kim Stanley |
| 4 | 0.956 |     Rowling, J.K.     |
| 5 | 0.952 |     Stephen, King     |


That's not so bad at least. There are a fair number of authors further down the list (I don't know if I've mentioned this, but I have 35 authors and over 200 books in my sample set). But it's still not perfect. It's still pretty interesting to see though.

Well, I think that about wraps up this series. It's about how I found it when doing my undergraduate research: interesting and you can get some neat results, but ultimately you have to do a fair bit of tuning to get any meaningful results. I hope you found it as interesting as I did.

As always, if you'd like to see the full source code for this post, you can find it on GitHub: <a title="authorship attribution source code" href="https://github.com/jpverkamp/small-projects/tree/master/authorship">authorship attribution</a>