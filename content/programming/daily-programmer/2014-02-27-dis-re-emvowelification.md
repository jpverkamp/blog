---
title: Dis/re-emvowelification
date: 2014-02-27 14:00:21
programming/languages:
- Racket
- Scheme
programming/sources:
- Daily Programmer
programming/topics:
- Dictionary
- Trees
- Trie
- Word Games
slug: disre-emvowelification
---
So far this week we've had a pair of related posts at the DailyProgrammer subreddit[^1]:

* [[02/24/14] Challenge #149 [Easy] Disemvoweler](http://www.reddit.com/r/dailyprogrammer/comments/1ystvb/022414_challenge_149_easy_disemvoweler/)
* [[02/26/14] Challenge #150 [Intermediate] Re-emvoweler 1](http://www.reddit.com/r/dailyprogrammer/comments/1yzlde/022614_challenge_150_intermediate_reemvoweler_1/)


Basically, if you're given a string with vowels, take them out. If you're given one without vowels, put them back in. One of the two is certainly easier than the other[^2]. :)

<!--more-->

To start off, we need a definition for what exactly a vowel is. That's a bit of a question in and of itself, but we'll go with the easiest definition:

```scheme
; For this case, y/w are not vowels. Also, latin characters only :smile:
(define vowels '(#\a #\e #\i #\o #\u))
(define (char-vowel? c) (member c vowels))
```

Straight forward enough. And it turns out that's enough to write the first function of the day:

```scheme
; Remove all vowels and non-alphabetic characters
(define (disemvowel str)
  (list->string
   (for/list ([c (in-string str)]
              #:when (and (char-alphabetic? c)
                          (not (char-vowel? c))))
     c)))
```

A few test cases:

```scheme
> (disemvowel "hello world")
"hllwrld"
> (disemvowel "this is a test!")
"thsstst"
> (disemvowel "this is a sparta")
"thsssprt"
```

Seems good. It turns out that there's a reason this is an easy challenge. Now to the more ~~difficult~~ fun one. Like many of the previous <a href="http://blog.jverkamp.com/tag/word-games/">word games</a> I've worked out, the data structure we need is a [[wiki:trie]](). Since it's been a while, I went ahead and re-implemented one:

```scheme
; Load a dictionary as a trie, cache the result
(define dictionary
  (let ([rhash #f])
    (thunk
      (when (not rhash)
        (set! rhash (make-hash))
        (with-input-from-file "enable1.txt"
          (thunk
            (for ([word (in-lines)])
              (hash-ref!
               (for/fold ([rhash rhash]) ([c (in-string word)])
                 (hash-ref! rhash c (make-hash)))
               'end
               #t)))))
      rhash)))
```

There's some pretty strange stuff going on there, so let's take it one chunk at a time. The outermost part is just caching the result. We've done that before. Inside of the `when`, we first create the hash, then open the dictionary. It's this part that's particularly fancy:

```scheme
(for ([word (in-lines)])
  (hash-ref!
   (for/fold ([rhash rhash]) ([c (in-string word)])
     (hash-ref! rhash c (make-hash)))
   'end
   #t))
```

What's that do? Well, as is often the case in Scheme, start on the inside:

```scheme
(for/fold ([rhash rhash]) ([c (in-string word)])
  (hash-ref! rhash c (make-hash)))
```

`for/fold` will loop over the parameters in the second set (characters `c` in this case) using each body to update the first variable (the recursive part of the hash `rhash`). As a second trick, because we're using {{< doc racket "hash-ref!" >}}, we find the recursive hash if there was already one or create a new one if there wasn't.

So that will recursively build the trie, but what's that bit around it, with another `hash-ref!`? Well, because `for/fold` returns the final state of the fold variable, we'll have the innermost hash. So just set the special key `end` to signify that this is a valid end to a word.

And that's it, we have a trie. Let's see what we can do with it.

Basically, we're going to recur down the characters in our input. At each character, we're going to have three possibilities:


* We're at the end of a word
* The consonant is the next character in the output
* A vowel is the next character in the output


Around that, we'll have a loop keeping the current remaining characters, the characters in the current word thus far, all of the words we've found thus far (which we could instead have done recursively, although we'd lose [[wiki:tail recursion]]() at that point), and the current location in the dictionary trie we built above. Something like this:

```scheme
(let loop ([chars (string->list str)]
           [current-word '()]
           [current-phrase '()]
           [current-dict (dictionary)])
  ; If we're at end of a word, add it and onwards
  ...
  ; Recur if we have a next non-vowel
  ...
  ; Check any vowel-only conditions by recurring
  ...)
```

To stay consistent, we need to know what we're going to be returning. Let's always return a list of possibilities. If we can't find any word lists at this point, return `'()`. Otherwise, a list of lists of words.

Assuming that all holds, let's write out each block. First is simple enough. If the `current-dict` shows the special key `end`, we have a word. Both the `current-word` and `current-phrase` are lists (built in reverse order), so make sure to keep that in mind:

```scheme
; If we're at end of a word, add it and onwards
(if (and (hash-ref current-dict 'end #f)
         (not (andmap char-vowel? current-word)))
    (loop chars
          '()
          (cons (list->string (reverse current-word)) current-phrase)
          (dictionary))
    '())
```

Two possibilities: either we're at the end of the word or we're not. If we are, we don't use up a character, so leave `chars`. Reset the `current-word` and add it to `current-phrase` instead. Likewise, because we've finished the word, we want to reset the `dictionary` to its original state. Since this function caches, there isn't much of a performance hit to doing it this way.

If not? Well this case doesn't care what's happening. Just return an empty list.

Next case, use the next non-vowel from the input:

```scheme
; Recur if we have a next non-vowel
(if (and (not (null? chars))
         (hash-ref current-dict (car chars) #f))
    (loop (cdr chars)
          (cons (car chars) current-word)
          current-phrase
          (hash-ref current-dict (car chars)))
    '())
```

The structure is much the same. If we're not out of characters and the next character is in the `current-dict` (which is the beauty of the trie: we know right here if we can progress or not), then loop. We eat up a char from `chars`, adding it to `current-word` and recurring down the `current-dict`. The `current-phrase` is unmodified.

Then, the last case. Since we don't have any vowels, at each point we should be able to insert any of them that makes sense. Like in the previous case, check against the `current-dict`:

```scheme
; Check any vowel-only conditions by recurring
(for/list ([c (in-list vowels)]
           #:when (hash-has-key? current-dict c))
  (loop chars
        (cons c current-word)
        current-phrase
        (hash-ref current-dict c)))
```

The only difference is that this time we don't use up a char from `chars`, because those are the consonants.

So, that should be all we need, right?

...

Nope!

We forgot pretty much the most important part of recursion--that one part that without which you're guaranteed[^3] to never terminate: a base case!

When do we know we can stop? Well, we can only stop when we've used up all of the `chars`, but that's not it. We also have to make sure that we don't have a current word in progress. So something like this:

```scheme
; Base case, used the entire input, no pending words
(if (and (null? chars)
         (null? current-word))
    (list (string-join (reverse current-phrase) " "))
    '())
```

Here we can also put together the phrases in pretty much the same way we did the words. Reverse the list since we built it up tail recursively and stick them together.

So what does it look like all together?

```scheme
; Take a string of characters sans vowels and figure out all possible phrases that it could have been
(define (reemvowel str)
  (let loop ([chars (string->list str)]
             [current-word '()]
             [current-phrase '()]
             [current-dict (dictionary)])
    (apply
     append
     ; Base case, used the entire input, no pending words
     (if (and (null? chars)
              (null? current-word))
         (list (string-join (reverse current-phrase) " "))
         '())
     ; If we're at end of a word, add it and onwards
     (if (and (hash-ref current-dict 'end #f)
              (not (andmap char-vowel? current-word)))
         (loop chars
               '()
               (cons (list->string (reverse current-word)) current-phrase)
               (dictionary))
         '())
     ; Recur if we have a next non-vowel
     (if (and (not (null? chars))
              (hash-ref current-dict (car chars) #f))
         (loop (cdr chars)
               (cons (car chars) current-word)
               current-phrase
               (hash-ref current-dict (car chars)))
         '())
     ; Check any vowel-only conditions by recurring
     (for/list ([c (in-list vowels)]
                #:when (hash-has-key? current-dict c))
       (loop chars
             (cons c current-word)
             current-phrase
             (hash-ref current-dict c))))))
```

The only new parts should be that `(apply append ...)` in there. That's to put everything together. Since each of the cases returns a list of phrases, we can just stick them all together.

So let's try it out:

```scheme
> (reemvowel (disemvowel "this is a sparta"))
...
...
...
```

Yeah... that's taking a while. Which makes sense if you think about it. With only 8 letters, (`"thsssprt"`), that's still a heck of a lot of words. As a bit of a side note, you can figure out how many words are made up of each consonant once and all vowels otherwise using a few command line tools [^4]:

```bash
egrep "^[aeiou]*t[aeiou]*$" enable1.txt | wc -l
28
```

Do the same for the rest of the letters:


| t | 28 |
|---|----|
| h | 18 |
| s | 21 |
| p | 15 |
| r | 35 |


Put that all together, and you have *28*18*21*21*21*15*35*28 ≅ 68 billion* combinations... and that doesn't even include words with two of the consonants. Or for that matter, words with only vowels...

Wait. Those might cause a problem... Technically, I've already solved it. Did you catch when? Take a look back up at the first subcase, where we were at the end of words:

```scheme
(not (andmap char-vowel? current-word))
```

So we can't have a word with all vowels. Technically, this rules out a few particularly useful words like `a` (along with a few less useful ones), but so it goes.

Anyways, we can't get all of those combinations, so what about a smaller test:

```scheme
> (reemvowel (disemvowel "hi"))
'("ha" "he" "hi" "ah" "oh" "ooh" "uh")
```

Seems to be working. Two consonants?

```scheme
> (reemvowel (disemvowel "good"))
'("go die" "go do" "go idea" "god" "good" "ago die" "ago do" "ago idea")
```

Now we can get either single letters or doubles. We have the original 'phrase' though, we it seems to be working.

Still, it would be nice to play with longer phrases. How can we do it?

Well, what if we didn't care about finding all of the possible phrases? What if any one of them would be fine? Well, it turns out that's not that big a change to make. We've already done it in a few blog posts before: use {{< doc racket "let/ec" >}}.

```scheme
; Take a string of characters sans vowels and figure out a possible phrase
(define (reemvowel/first str)
  (let/ec return
    (let loop ([chars (string->list str)]
               [current-word '()]
               [current-phrase '()]
               [current-dict (dictionary)])
      ; Out of input and no current word? Found a phrase!
      (when (and (null? chars)
                 (null? current-word))
        (return (string-join (reverse current-phrase) " ")))
      ; If we're at end of a word, add it and onwards
      (when (and (hash-ref current-dict 'end #f)
                 (not (andmap char-vowel? current-word)))
        (loop chars
              '()
              (cons (list->string (reverse current-word)) current-phrase)
              (dictionary)))
      ; Recur if we have a next non-vowel
      (when (and (not (null? chars))
                 (hash-ref current-dict (car chars) #f))
        (loop (cdr chars)
              (cons (car chars) current-word)
              current-phrase
              (hash-ref current-dict (car chars))))
      ; Check any vowel-only conditions by recurring
      (for ([c (in-list (shuffle vowels))]
            #:when (hash-has-key? current-dict c))
        (loop chars
              (cons c current-word)
              current-phrase
              (hash-ref current-dict c))))))
```

We no longer care what're we're returning, so we don't need all of those `if`s. Instead, we just keep going until we find a valid string and `return` it. But strictly speaking, it's not a 'return', it's a [[wiki:continuation]](). For all Racket cares, we could have just as well have called it `steve` or `ዱᓹዲțũഓળƝف`[^5][^6][^7]. In any case, that should run rather faster:

```scheme
> (reemvowel/first (disemvowel "this is sparta"))
"thae sei si sprout"
> (reemvowel/first (disemvowel "hello world"))
"he lo lwei rule do"
```

There's still a bit of a bias that I'd like to get rid of[^8], but I think that's good enough for a post. Like always, you can get the whole source on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/disreemvowel.rkt">disreemvowel.rkt</a>

[^1]: Also, it's a great excuse for a crazy title
[^2]: Exercise for the reader: which is which :smile:
[^3]: Well, most of the time...
[^4]: I'm sure there's a better way to do that
[^5]: Racket uses Unicode by default, it's awesome
[^6]: `(list->string (for/list ([i (in-range 10)]) (integer->char (random #x1800))))`
[^7]: I hope that doesn't actually mean anything...
[^8]: Exercise for the reader...
