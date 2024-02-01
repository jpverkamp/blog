---
cover: /embeds/books/the-rhai-book.jpg
date: '2024-01-26'
goodreads_id: 122858878
rating: 4
reviews/authors:
- Stephen Chung
reviews/lists:
- 2024 Book Reviews
title: 'The Rhai Book'
---
[Rhai](https://rhai.rs/) is a scripting language written in and generally used by the programming language Rust when you want something a bit more dynamic/don't want to recomile. 

The Rhai book is the [mdBook](https://github.com/rust-lang/mdBook) style documentation that describes the language, gets into how to use it (in both straight forward and more complicated scenarios), and acts as a reference when needed. 

It's a bit of an odd one to read straight through, but I've been looking for exactly this sort of thing (an embeddable scripting language for Rust) so I figured I'd give it a chance!

<!--more-->

Languagewise, the upside is the tight integration with Rust. Downsides are that it will never be as fast as some things like JS or Lua, since (in addition to being a much smaller target market), it's just a different style of language. No JIT, not even a VM. But you don't always need that!

Bookwise, the initial introduction and examples are solid and a good introduction. Then we get a section on Rust integration which is entirely necessary but goes far further than I expect to need. The section after ('Scripting Language') feels a fair bit repetitive when compared to the introduction and I'd probably have swapped this and the integration section. 

After that, several chapters of more advanced concepts are well placed and a deep dive into all sorts of interesting ideas both for Rhai specifically and programming language design more generally. I find the currying style built directly into functions--and then used to implement closures--to be particularly neat. I may steal that one day. 

And the language reference--don't read that straight through, that's not what it's for. :smile:

Overall, a neat language and a neat read. Let's see what we can do with it!