---
title: raco pkg install noise 
date: 2021-08-05
programming/languages:
- Racket
- Scheme
programming/topics:
- Games
- Graphics
- Mathematics
- Noise
---
What feels like a million years and a lifetime ago, I wrote up a [library for perlin and simple noise in Racket]({{< ref "2013-04-11-perlin-and-simplex-noise-in-racket" >}}). Inspired by [Jens Axel Søgaard's new Sketching library](https://github.com/soegaard/sketching) (processing in Racket) and a conversation thereabout, I figure it's about time to push noise to the `raco` package manager!

<!--more-->

https://pkgd.racket-lang.org/pkgn/package/noise

```bash
$ raco pkg install noise

Resolving "noise" via https://download.racket-lang.org/releases/8.1/catalog/
Resolving "noise" via https://pkgs.racket-lang.org
Downloading repository https://github.com/jpverkamp/noise.git#master
raco setup: version: 8.1
raco setup: platform: aarch64-macosx [cs]
raco setup: target machine: tarm64osx
raco setup: installation name: 8.1
raco setup: variants: cs
raco setup: main collects: /Applications/Racket v8.1/collects/
...
Library/Racket/8.1/pkgs/noise/manual.scrbl:25:10: WARNING: no declared exporting libraries for definition
  in: perlin
Library/Racket/8.1/pkgs/noise/manual.scrbl:29:10: WARNING: no declared exporting libraries for definition
  in: simplex?
raco setup: --- installing collections ---                         [17:26:35]
raco setup: --- post-installing collections ---                    [17:26:35]
```

It's alive!

I still have to figure out how to get it to see the documentation, but that's pretty cool. I should really get back into Racket. It's a fun language for a lot of things. 