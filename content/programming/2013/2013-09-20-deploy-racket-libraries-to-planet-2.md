---
title: Deploy Racket libraries to Planet 2
date: 2013-09-20 14:00:23
programming/languages:
- Racket
- Scheme
---
Over the last few years, I've managed to write a fair bit of Racket code. It's a lovely language and an even better ecosystem for writing quick/clean code ({{< doc racket "batteries included!" >}}). Several times throughout that, I've written code that I thought could be useful to others, including several libraries that I used to write my [Racket Roguelike]({{< ref "2013-03-28-writing-a-roguelike-in-racket-day-0.md" >}}) and code that I've used working with the C211 class at Indiana University. I've always said that I should turn these into packages that others can use and... I've finally figured it out.

<!--more-->

Part of the reason that I finally figured it out is the introduction of the new and improved Planet 2 framework (currently in beta). Theoretically, it makes creating a library as simple as publishing the GitHub URL it's hosted at. In practice, it's a bit more complicated than that, but not much.

When I finally set about working on this, my first stop was <a href="http://lists.racket-lang.org/dev/archive/2012-November/010768.html">this message</a> from Jay McCarthy on the Racket mailing list. Essentially, it announced the beta release and has temporary documentation <a href="http://faculty.cs.byu.edu/~jay/tmp/20121108-pkgs/planet2/index.html">here</a> which got me started. Specifically, it said that I should be able to just put a package in GitHub and then install it on any machine with this command:

```bash
raco pkg install github://github.com/{username}/{package-name}/{branch}/
```

After that, there was a lot of chatter about fixing the idea that a package had to actually be a collection containing one or more packages. Since most of my code is one package per collection, I would love to see this work, but I haven't figured it out yet. That means that to work, each repository has to have a folder with the same name at the top level. So the general layout (for me at least) looks something like this:

```bash
github://jpverkamp/{package}
+ info.rkt
+ manual.scrbl 
+ {package}
  + main.rkt
  + other-file.rkt
  + ...
```

Strictly speaking, the info and manual files aren't necessary, but they seem useful. Here's some documentation for creating an info.rkt file ({{< doc racket "linky" >}}) and here's some on creating documentation with Scribble ({{< doc racket "linky" >}}). I'm really liking how Scribble works; I'm actually thinking about reworking this blog to be statically generated using it (similar to Greg Hendershott's <a href="https://github.com/greghendershott/frog">frog project</a>). We'll see.

In any case, once all of those files are in place, it really is that easy. Push all of those files to GitHub and the command earlier works just fine. About the only problem I've seen so far is that occasionally the timestamps get strange. That leads to Dr. Racket (but not the command line version) complaining about the timestamps on the .zo files and refusing to run. Wait until the match though and everything is golden.

That being said, I've gone through and started to push out some libraries (along with updating my code to use them). It's certainly cleaner than using Git submodules (which Racket Roguelike originally did), especially if several projects use the same library. We'll see if it continues to be so easy.

So far, I've converted / written these five libraries:

|   Library    | Source | Docs |                                                                                              Description                                                                                               |
|--------------|--------|------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ascii‑canvas |  src   | docs | ascii-canvas simulates a code page 437 ASCII terminal display. It supports all 256 characters of codepage 437, arbitrary foreground colors, arbitrary background colors, and arbitrary terminal sizes. |
|  bit‑struct  |  src   | docs |                  Extend standard Racket structs for bitfields. It creates the normal accessors for structure along with defining three new methods: `build‑*`, `*‑>bytes`, `bytes‑>*`                  |
|     c211     |  src   | docs |                 c211 provides a Racket version of the C211 libraries used in Wombat. So far, the following libraries are (mostly) complete: `c211/color`, `c211/image`, `c211/matrix`                  |
|    noise     |  src   | docs |                  This package provides Racket versions of the [[wiki:Perlin noise|Perlin]]() and [[wiki:Simplex noise|Simplex]]() noise generators.                  |
|    thing     |  src   | docs |                                                                This package provides a simple prototype object-based system for Racket.                                                                |

To install any of these libraries (unless otherwise mentioned), it really is as easy as running this command:
`raco pkg install github://github.com/jpverkamp/**{library name}**/master`

Alternatively, you can do it directly from DrRacket:

```scheme
> (require pkg)
> (install "github://github.com/jpverkamp/{library name}/master
```

Either way, after the code runs, you can require the library directly:

```scheme
> (require pkg)
> (install "github://github.com/jpverkamp/noise/master")
...
> (require noise)
> (perlin 8.6 7.5 3.09)
0.49156684001488843
```

Using the latter, I've gotten a few errors, but it seems to work regardless. I prefer the raco version anyways, so I didn't pay particularly much attention to them.

At the moment, that same list above lives at <a href="http://blog.jverkamp.com/lists/racket-libraries/ ‎">Lists > Racket Libraries</a>, although I can't guarantee that I won't move it if/when I ever finish my blog redesign / shift to static pages that I've been working on for a few months. We'll see. For now though it seems like a reasonable enough place though.