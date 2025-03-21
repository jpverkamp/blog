---
title: Call stack bracket matcher
date: 2014-06-11 14:00:55
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
---
<a href="http://programmingpraxis.com/2014/06/10/balanced-delimiters-2/">Five minute post</a> from Programming Praxis:


> Write a function to return true/false after looking at a string. Examples of strings that pass:

> `{}, [], (), a(b)c, abc[d], a(b)c{d[e]}`

> Examples of strings that don’t pass:

> `{], (], a(b]c, abc[d}, a(b)c{d[e}]`


<!--more-->

The basic idea you have to deal with here is that you need a stack of which brackets you're matching. It's easy enough if there's only one pair, but what if you have two nested pairs:

`a(b[c]d)e`

Then, once you hit the opening `(`, you have to look for a `)`, but once you see the `[`, you need to see a `]` *first*, while still looking for the `)` after. Sounds like a stack for me. 

It would be perfectly acceptable to keep a stack around as a variable and loop over the string. Heck, that's what I did in <a href="https://github.com/jpverkamp/wombat-ide/blob/master/ide/src/wombat/gui/text/BracketMatcher.java">Wombat's bracket matcher</a>. But since we're working with Scheme, let's do something a little more recursive:

```scheme
(define (match-brackets [matching #f])
  (define pairs '((#\( . #\)) (#\{ . #\}) (#\[ . #\])))
  (define c (read-char))
  (cond
    [(eof-object? c)            (not (not matching))]
    [(assoc c pairs)            => (λ (pair) (and (match-brackets (cdr pair)) 
                                                  (match-brackets matching)))]
    [(eq? c matching)           #t]
    [(member c (map cdr pairs)) #f]
    [else                       (match-brackets matching)]))
```

'But what?' you might say, where is the stack? How do we remember the first bracket we're matching when we get to the second? Well that's the beauty of the stack. Easy time we see a bracket (the second case of the `cond`), we recur with the new matching character. That call will short circuit if it sees the matching bracket (the third case), a mismatched bracket (the fourth), or an early end of string (the first, only returning valid if we're in the outermost part of the loop where `matching` is `#f`). 

And that's pretty much it. One last trick is that we also get implicit position within the string, because of the state maintained by `read-char`, so we don't even have to explicitly recur down the string. Just calling `match-brackets` will do it for us, and sequential calls (as in the second case) work as they need to.

Shiny!

Source: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/match-brackets.rkt">match-brackets.rkt</a>