---
title: Learn You a Haskell for Great Good!
date: 2020-01-29
generated: true
reviews/lists:
- 2020 Book Reviews
reviews/authors:
- "Miran Lipova\u010Da"
goodreads_id: 6593810
cover: /embeds/books/learn-you-a-haskell-for-great-good.jpg
rating: 4
page_count: 176
---
This is a re-read, although it's a been a few years. Actually, those years seem to have rather helped. Last time I around, I was reading through and everything made a lot of sense (I have a strong background in functional programming, so it wasn't new here). And then I hit monads and side effects and everything went bizarre.  

This time around? Well, everything still went sideways, but in a way that made sense?  

<!--more-->

```haskell
moveKnight :: KnightPos -> [KnightPos]
moveKnight (c,r) = do
    (c',r') <- [(c+2,r-1),(c+2,r+1),(c-2,r-1),(c-2,r+1), c+1,r-2),(c+1,r+2),(c-1,r-2),(c-1,r+2)]
    guard (c' `elem` [1..8] && r' `elem` [1..8])
    return (c',r')  
```

Sure.  

In any case, if you're into programming, particularly functional programming, you should give Haskell a chance. It probably won't become your default goto language, but it might just give you a new way to think, which is always worthwhile. And [[Learn You a Haskell for Great Good!]]() is a great way to do that. It's well written and funny, bringing you through at least enough of the language to decide just how much more you want to dive in.  

I think the primary thing missing is any solid, practical real world examples. Mathematical tricks and trivial problems are all well and good, but if that's all you can write in a language, you're not going to be doing much with it.  

Still worth a read.