---
title: Dictionary tries in Racket
date: 2012-10-11 13:55:38
programming/languages:
- Racket
- Scheme
programming/topics:
- Data Structures
- Word Games
---
For the next few posts, we're going to need a way to represent a dictionary. You could go with just a flat list containing all of the words in the dictionary, but the runtime doesn't seem optimal. Instead, we want a data structure that lets you easily get all possible words that start with a given prefix. We want a {{< wikipedia "trie" >}}.

{{< figure src="/embeds/2012/trie_example.png" >}}.
Source: [dictionary source code](https://github.com/jpverkamp/small-projects/blob/master/racket-libraries/dictionary.rkt)
