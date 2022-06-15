---
title: Writing An Interpreter In Go
date: 2021-12-03
reviews/lists:
- 2021 Book Reviews
reviews/authors:
- Thorsten Ball
goodreads_id: 32681092
cover: /embeds/books/writing-an-interpreter-in-go.jpg
rating: 5
page_count: 200
---
You know, I'm always up for a good 'writing an interpreter' book. Making programming languages is a thing I've done a number of times before and really have been itching to get back into again. Add to that a desire to pick up a bit more Go syntax... well, perhaps this book is just about perfect. 

In a nutshell, it's a 'writing an interpreter' book. They go through lexing, parsing, and evaluating. On a plus side, they include closures and first-class functions. On the downside, they specifically didn't get into garbage collection:

> Unfortunately, no. We'd have to disable Go's GC and find a way to take over all of its duties. That's easier said than done. It's a huge undertaking since we would also have to take care of allocating and freeing memory ourselves - in a language that per default prohibits exactly that.
> 
> That's why I decided to not add a "Let's write our own GC next to Go's GC" section to this book and to instead reuse Go's GC. Garbage collection itself is a huge topic and adding the dimension of working around an existing GC blows it out of the scope of this book. But still, I hope that this section gave you a rough idea of what a GC does and which problems it solves. Maybe you even know now what to do if you were to translate the interpreter we built here into another host language without garbage collection.

Fair enough. Something to think about when I get that far. 

I think the weakest part of the book is just *how much* time is spent showing the tests failing every single time. It gets old. Finally around `let` statements, there are a few that don't, but it really isn't something I felt the book needed. On the other hand, that's a relatively minor quibble and they're easy enough to skip. 

On the other other hand, running throughout the book the sense of humor is wonderful. 

> In ten years, when Monkey is a famous programming language and the discussion about research-ignoring dilettantes designing programming languages is still ongoing and we're both rich and famous, someone will ask on StackOverflow why integer comparison in Monkey is slower than boolean comparison. The answer will be written by either you or me and one of us will say that Monkey's object system doesn't allow pointer comparison for integer objects. It has to unwrap the value before a comparison can be made. Thus the comparison between booleans is faster. We'll add a "Source: I wrote it." to the bottom of our answer and earn an unheard of amount of karma. 

Overall, if you're looking for a solid introduction to writing an interpreter that goes into a decent amount of depth, this is a solid choice. Especially if Go is already something you're familiar with. Onward!