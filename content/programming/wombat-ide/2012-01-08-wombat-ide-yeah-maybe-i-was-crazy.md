---
title: Wombat IDE - Yeah... Maybe I was crazy
date: 2012-01-08 04:55:26
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
So I started `let` today. And let me tell you (no pun intended) that is one sticky function to work with, once you get the entire family involved. You have let, let*, let-values, letrec, and named lets, along with all sorts of combinations thereof. I actually made it about 90% through all of these (just a few bugs to work out in letrec) before I realized that this was perhaps more than I actually wanted to do for the public version of Wombat.

<!--more-->

I need a working version of Wombat when the new semester starts, preferably one that's already compatible with Chez Scheme. So I think I'm going to bite the bullet and look into bundling a native version of Petite with Wombat and wrapping that as the Scheme back-end. That's how [Odete did it]({{< ref "2011-07-07-wombat-ide-a-bit-of-history.md" >}}), using a native interface in their case, but I think I'm just going to use either the local network or even just `stdin` and `stdout` to communcate. We'll see how that goes.

Of course, I'll keep the entire code base for Wombat Scheme in the repository if I ever want to deal with it again. It was definitely an interesting project and taught me a little more about how much work it takes to actually implement a language. We'll see where that goes from here.