---
title: The Algorithmic Beauty of Plants
date: 2021-04-04 00:00:00
generated: true
reviews/lists:
- 2021 Book Reviews
reviews/authors:
- "Przemys\u0142aw Prusinkiewicz"
goodreads_id: 944626
cover: /embeds/books/the-algorithmic-beauty-of-plants.jpg
isbn: 0387972978
isbn13: '9780387972978'
rating: 5
---
This... was a somewhat unepxected read.  

Essentially, it's a textbook about how [Lindenmayer systems (L-Systems)](https://en.wikipedia.org/wiki/L-system) can be used to simulate and model plants in increasingly complicated ways.  

<!--more-->

In a nutshell, L-Systems are a series of rewriting rules that are applied over and over again. For example:  

![Plants-1-04](/embeds/books/attachments/plants-1-04.png)  

Figure a shows that if you replace `F` with `F[+F]F[-F]F`, where `F` means draw a line, `[` and `]` control branches, and `+` and `-` branch left and right, that alone is enough to give you that nice branching structure. the same for the other more complicated patterns.  

They do get more complicated from there, including things like parameters (`F(1)` is move forward one, otherwise you can rotate by various angles that changes as you go along):  

![Plants-1-06](/embeds/books/attachments/plants-1-06.png)  

You can even get into full 3D models:  

![Plants-1-10](/embeds/books/attachments/plants-1-10.png)  

It's kind of amazing how relatively accurately you can model all sorts of plants and even simple animal cells with this. And this book goes a long way towards building this up for you.  

All that being said, it does get very very mathy at times:  

![Plants-1-02](/embeds/books/attachments/plants-1-02.png)  

It's the sort of thing that I love, but you really should remember: this is a textbook. It reads like one. I wonder if there are any online classes to follow along using this book. Something work looking at.  

In any case, if you're looking for a textbook about how L-Systems can model plants and just how complicated L-Systems can get (while still maintaining their 'order from a few short rules'), this is a great book. Well worth the read.