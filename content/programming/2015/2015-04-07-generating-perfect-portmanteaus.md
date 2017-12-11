---
title: Generating perfect portmanteaus
date: 2015-04-07
programming/languages:
- Racket
programming/topics:
- Word Games
---
A quick programming post, since it's been a while, inspired by this video:

{{< youtube QVn2PZGZxaI >}}

I'm not going to go quite as far as that, but I thought it would be interesting to write up some quick code to generate portmanteaus[^1].

<!--more-->

Basically[^2], a portmanteau is a combination of two words, smooshing them together[^3] and dropping some letters from each. In this case, what I'm specifically interested in is 'perfect' portmanteaus (I'm not sure if there is a better term for it), where the suffix of one word exactly matches the prefix of the other.

As an example, consider the words `hamster` and `termine`. The last three letters of the former, perfectly matches the first three of the latter, so let's overlap them. `hamstermite`. Bam.

So how do we do it?

```racket
(define current-minimum-overlap (make-parameter 3))

(define (portmanteau left right)
  (define maximum-overlap (- (min (string-length left) (string-length right)) 1))

  (for*/first ([overlap (in-range maximum-overlap (- (current-minimum-overlap) 1) -1)]
               #:when (equal? (substring left (- (string-length left) overlap))
                              (substring right 0 overlap)))
    (list left
          right
          (string-append
           (substring left 0 (- (string-length left) overlap))
           right))))
```

Should be straight forward enough. Basically, we start with the longest possible overlap (1 less than the length of the shorter word, since we don't want to completely subsume a word), counting down until we reach some minimum overlap. For each possible sequence, we compare the prefix and suffix of the two words, only proceeding into the body of the loop when they match. That's the beauty of {{< doc racket "for*/first" >}}, it will loop until it gets a valid value, returning when it does.

And that's really it. Try it out with the example from earlier:

```racket
> (portmanteau "hamster" "termite")
'("hamster" "termite" "hamstermite")
```

Since that was so quick, let's put some simple wrapper code around it in order to find all portmanteaus from a given word list. First, do the heavy lifting of finding portmanteaus:

```racket
(define (portmanteaus)
  (define words
    (for*/list ([raw-line (in-lines)]
                [line (in-value (string-trim (string-downcase raw-line)))]
                #:when (not (equal? "" line)))
      line))

  (for*/list ([left (in-list words)]
              [right (in-list words)]
              #:when (not (eq? left right))
              [portmanteau (in-value (portmanteau left right))]
              #:when portmanteau)
    portmanteau))
```

{{< doc racket "in-value" >}} is useful in {{< doc racket "for*" >}} since it lets you bind a single value for future `#:when` blocks without having to recalculate anything.

After that, a wrapper to process some command line parameters and render output in a few different ways:

```racket
(define paths
  (command-line
   #:program "portmanteau"
   #:once-each
   [("--minimum-overlap")
    overlap
    "Specify the minimum necessary overlap (default = 3)"
    (cond
      [(string->number overlap) => current-minimum-overlap]
      [else (error '--minimum-overlap "must specify a number")])]
   #:once-any
   [("--verbose")
    "Print in verbose mode (default = false)"
    (verbose-mode #t)]
   [("--graph")
    "Print out a dotfile"
    (graph-mode #t)]
   #:args paths

   paths))

(when (null? paths)
  (set! paths '("-")))

(for ([path (in-list paths)])
  (define results
    (cond
      [(equal? path "-")
       (portmanteaus)]
      [else
       (with-input-from-file path portmanteaus)]))

  (define g (unweighted-graph/directed '()))

  (for ([result (in-list results)])
    (match-define (list left right portmanteau) result)
    (cond
      [(verbose-mode)
       (printf "~a + ~a = ~a\n" left right portmanteau)]
      [(graph-mode)
       (add-edge! g (~a "\"" left "\"") (~a "\"" right "\""))]
      [else
       (displayln portmanteau)]))

  (when (graph-mode)
    (displayln (graphviz g))))
```

Now you can do some interesting things:

```bash
$ racket portmanteau.rkt animals.txt

brown recluse spider monkey
gila monstermite
grasshopperegrine falcon
hamstermite
leechidna
ottermite
```

Just in case you cannot figure out what animals actually went into that list:

```bash
$ racket portmanteau.rkt --verbose animals.txt

brown recluse spider + spider monkey = brown recluse spider monkey
gila monster + termite = gila monstermite
grasshopper + peregrine falcon = grasshopperegrine falcon
hamster + termite = hamstermite
leech + echidna = leechidna
otter + termite = ottermite
```

Or if you want to be a little more general, matching with only 2 characters rather than the default 3:

```bash
$ racket portmanteau.rkt --minimum-overlap 2 --verbose animals.txt

armadillo + loon = armadilloon
armadillo + lorikeet = armadillorikeet
armadillo + louse = armadillouse
black mamba + badger = black mambadger
brown bear + armadillo = brown bearmadillo
brown recluse spider + spider monkey = brown recluse spider monkey
chinchilaa + aardvark = chinchilaardvark
copperhead snake + kestrel = copperhead snakestrel
coyote + termite = coyotermite
crow + owl = crowl
eagle + leech = eagleech
eagle + leopard seal = eagleopard seal
echidna + narwhal = echidnarwhal
gecko + koala = geckoala
gila monster + termite = gila monstermite
grasshopper + peregrine falcon = grasshopperegrine falcon
hamster + termite = hamstermite
hyena + narwhal = hyenarwhal
jackal + albatross = jackalbatross
king cobra + rattlesnake = king cobrattlesnake
king cobra + raven = king cobraven
kingsnake + kestrel = kingsnakestrel
kiwi + wild boar = kiwild boar
leech + chinchilaa = leechinchilaa
leech + echidna = leechidna
leopard seal + albatross = leopard sealbatross
narwhal + albatross = narwhalbatross
ostrich + chinchilaa = ostrichinchilaa
otter + termite = ottermite
polar bear + armadillo = polar bearmadillo
rattlesnake + kestrel = rattlesnakestrel
sloth bear + armadillo = sloth bearmadillo
snapping turtle + leech = snapping turtleech
snapping turtle + leopard seal = snapping turtleopard seal
sparrow + owl = sparrowl
sperm whale + leech = sperm whaleech
sperm whale + leopard seal = sperm whaleopard seal
sponge + gecko = spongecko
swan + anaconda = swanaconda
wild boar + armadillo = wild boarmadillo
```

Heh. Narwhalbatross. Wild boarmadillo. :smile:

And as a final bonus, using the <a href="https://github.com/stchang/graph/tree/master">graph</a> library I've used (and contributed to) before, we can render the structure of the thing):

```bash
$ racket portmanteau.rkt --graph --minimum-overlap 2 animals.txt \
    | sed "s/edge \[dir=none\];//g" \
    | fdp -Tpng > animals.png \
    && open animals.png
```

{{< figure src="/embeds/2015/animals.png" >}}

Fun. :)

Think of the arrows as going from the stuck on word to where it's sticking rather than in the order the words would be written. It's easy enough to change though if you'd like, just swap the arguments in the `add-edge!` call above.

And... that's it. Not much more to do with this one, unless I want to duplicate the above video and portmanteau all the things! We'll see.

As with all my code, you can see the entire thing on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/portmanteau.rkt">portmanteau.rkt</a>

[^1]: Apparently either portmanteaus or portmanteaux is a valid pluralization
[^2]: If you didn't watch the video--you really should; at least the introduction
[^3]: Yes, that is the technical term