---
title: Path to philosophy
date: 2013-03-28 14:00:05
programming/languages:
- Racket
- Scheme
programming/sources:
- Daily Programmer
programming/topics:
- Backtracking
- Graph Theory
- Graphs
- Wikipedia
- Word Games
---
Yesterday, <a title="Daily programmer sub-reddit" href="http://www.reddit.com/r/dailyprogrammer/">the daily programmer Subreddit</a> had <a title="[03/27/13] Challenge #121 [Intermediate] Path to Philosophy" href="http://www.reddit.com/r/dailyprogrammer/comments/1b3ka1/032713_challenge_121_intermediate_path_to/">a post that</a> mirrored a problem I've often seen before: the idea that if you follow first links ((With some caveats)) on [[wiki:Main Page|Wikipedia]](), you eventually end with [[wiki:Philosophy]](). For example, if you follow the first links from [[wiki:Molecule]](), you get the following path:

> [[wiki:Molecule]]() → [[wiki:Atom]]() → [[wiki:Matter]]() → [[wiki:Rest Mass]]() → [[wiki:Invariant Mass]]() → [[wiki:Energy]]() → [[wiki:Kinetic Energy]]() → [[wiki:Physics]]() → [[wiki:Natural Philosophy]]() → [[wiki:Philosophy|Philosophy]]()

<!--more-->

I've followed the paths by hand before, but this is the first time that I've actually tried to do it in a programmatic manner. It's harder than you might think, but really only because of the crazy number of edge cases involved in correctly parsing either the <a title="MediaWiki" href="http://www.mediawiki.org/wiki/MediaWiki">MediaWiki </a>format or the resulting HTML. I eventually got it working though, and here's the result.

First, we want to be able to fetch the pages from Wikipedia. We really want to [[wiki:Cache (computing)|cache]]()these as we go, so that we don't accidentally get rate-limited by Wikipedia's servers (or at the very least to be nicer to them). Here's what I wrote for that part (using the <a title="Wikipedia API" href="http://www.mediawiki.org/wiki/API:Main_page">Wikipedia API</a>) ((If you'd like to follow along, here's the code on GitHub: <a title="GitHub: Path to philosophy source" href="https://github.com/jpverkamp/small-projects/blob/master/blog/path-to-philosophy.rkt">path to philosophy source</a>)):

```scheme
(define wikipedia-api-url "http://en.wikipedia.org/w/api.php?format=json&action=query&titles=~a&prop=revisions&rvprop=content")

; Fetch pages from Wikipedia, caching them to disk
(define (get-page title [skip-cache #f])
  ; If the file isn't cached, fetch it
  (define path (build-path cache (format "~a.json" title)))
  (when (or skip-cache (not (file-exists? path)))
    (define url (string->url (format wikipedia-api-url title)))
    (define http-in (get-pure-port url #:redirections 3))
    (define response (port->string http-in))
    (close-input-port http-in)
    (with-output-to-file path
      (lambda ()
        (display response))))

  ; Load the file from cache (assume the previous worked)
  (string->jsexpr (file->string path)))
```

> `UPDATE 2018-07-08`

> When fixing the below issue, I also found that I sometimes found pages that contained characters in the names that caused issues. Specifically `:` which doesn't work on Mac OS and `/` which doesn't work ever (since it's trying to create a subfolder). To fix it, we just strip out non-alphanumeric characters:

```scheme
; Fetch pages from Wikipedia, caching them to disk
(define (get-page title [skip-cache #f])
  ; If the file isn't cached, fetch it
  (define clean-title (regexp-replace* #rx"[^a-zA-Z0-9._-]+" title "-"))
  (define path (build-path cache (format "~a.json" clean-title)))
  ...
```

Basically, where ever your code is running from, it will create / use a subdirectory called *cache* into which it will dump one file per page, each with the *[[wiki:json]]()* extension duplicating whatever content that Wikipedia has returned. Technically, it has the ability to force a refresh, but in practice I just deleted the entire cache folder when I wanted to reset it ((Yes, I know. That kind of defeats the purpose of having a cache in the first place...)).

Unfortunately, once you have that, it's still in a nice nested structure. So we need to be able to pull out the actual page content. If you use <a title="Racket API: JSON" href="http://pre.racket-lang.org/docs/html/json/index.html">Racket's JSON library</a>, you'll have a nested series of {{< doc racket "hashes " >}}and {{< doc racket "lists" >}} that you have to navigate through. It's not quite as nice as <a title="Python JSON" href="http://docs.python.org/2/library/json.html">Python's model</a> ((Which I've used extensively <a title="Github: jsonq source" href="https://github.com/jpverkamp/jsonq">before</a>. How haven't I written a blog post about that yet?)) but it's not bad. Basically, I figured out the structure by hand and write a function to just ignore anything I didn't care about:

```scheme
; Extract the first page content from a JSON encoded Wikipedia API response
(define (get-first-page-content page)
  (define page-keys (hash-keys (hash-ref (hash-ref page 'query) 'pages)))
  (define content (hash-ref (hash-ref (hash-ref page 'query) 'pages) (car page-keys)))
  (hash-ref (car (hash-ref content 'revisions)) '*))
```

> `UPDATE 2018-07-08`

> This actually needs a fix. It seems the Wikipedia API will occasionally return 'missing pages'. To fix that, we need to detect those and return empty content for those pages. The backtracking we implement later will take care of skipping those pages.

```scheme
; Extract the first page content from a JSON encoded Wikipedia API response
(define (get-first-page-content page)
  (define page-keys (hash-keys (hash-ref (hash-ref page 'query) 'pages)))
  (define content (hash-ref (hash-ref (hash-ref page 'query) 'pages) (car page-keys)))
  (cond
    [(hash-has-key? content 'missing)
     (debug-printf "[DEBUG] missing content detected, skipping\n")
     ""]
    [else
     (hash-ref (car (hash-ref content 'revisions)) '*)]))
```

Now we have the actual content of the page in the original <a title="MediaWiki Syntax" href="http://www.mediawiki.org/wiki/Help:Formatting">MediaWiki syntax</a>. Links will look like this `[[target|text]]`, so we should just be able to write a simple [[wiki:regular expression]]() and we'll be golden, right? Well, not so much. There are a number of additional rules that we're supposed to follow:

* Take the first link in the main body of the page, except:
* Ignore links in parentheses
* Ignore links in italics
* Ignore links to images / files
* Ignore links in infoboxes, etc
* If a path doesn't work, backtrack and try the second link

So that gets a little more interesting. Originally, I tried to do everything with regular expressions. That took a few hours until I realized that no matter how close I was getting, the code was an unholy mess. It turns out that regular expressions are *not* the tool you want to use for non-regular languages (anything with nestable tags) ((Yes, I should have known this. I've taken probably a dozen classes in theory and/or programming languages. But you can actually do a pretty decent hack job of it if you make certain assumptions about your input...)). In any case, eventually I regained my senses and decided to go for a simple parser instead. All I needed was some way to match (potentially nested) tags with arbitrary delimiters ((MediaWiki uses at single and double square and curly braces. It's a little wild...)). Here's what I have for that:

```scheme
(define upper-bound (- (string-length page-content) 1))

; Does the string at a given position start with a given text
(define (text-at? pos str)
  (and (<= 0 pos upper-bound)
       (<= 0 (+ pos (string-length str)) (+ upper-bound 1))
       (equal? str (substring page-content pos (+ pos (string-length str))))))

; Return the position right after a closing bracket
; Ignore nested pairs
(define (find-matching open close start)
  (let loop ([position start] [nested 0])
    (define at-opening (and open (text-at? position open)))
    (define at-closing (and close (text-at? position close)))
    (cond
      [(> position upper-bound)
       position]
      [(and at-closing (= nested 0))
       (+ position 2)]
      [at-closing
       (loop (+ position 2) (- nested 1))]
      [at-opening
       (loop (+ position 1) (+ nested 1))]
      [else
       (loop (+ position 1) nested)])))
```

Basically, given a position in the `page-content` ((It's a free variable here; that's because these are actually nested in the actual main parsing function.)) and the starting / ending delimiters, find the correctly matching end. `nesting` is used to keep track of how many tested labels we have (mostly useful for `{{patterns like this}}`). So what do we do with all of that?

```scheme
; Filter out any links in the page that are in paranthesis, italics, or tables
; Return a list of all remaining internal links
(define (filter-links page-content)
  ...

  ; Pull out any links, ignoring certain patterns
  (define links
    (let loop ([position 0])
      (cond
        ; Done looking
        [(>= position (string-length page-content))
         '()]
        ; Found subcontent {{content}}, ignore it
        [(text-at? position "{{")
         (define end (find-matching "{{" "}}" (+ position 2)))
         (loop end)]
        ; Found bracketed italics content ''content'', ignore it
        ; Note: open #f because these can't next
        [(text-at? position "''")
         (define end (find-matching #f "''" (+ position 2)))
         (loop end)]
        ; Found paranthesis, ignore them
        [(text-at? position "(")
         (define end (find-matching "(" ")" (+ position 1)))
         (loop end)]
        ; Found a File/image block [[File/Image: content]], ignore it
        ; Note: may contain nested [[links]] we don't want
        [(or (text-at? position "[[File:")
             (text-at? position "[[Image:"))
         (define end (find-matching "[[" "]]" (+ position 2)))
         (loop end)]
        ; Found a link: [[content]], return it
        [(text-at? position "[[")
         (define end (find-matching "[[" "]]" (+ position 2)))
         (cons (substring page-content position end)
               (loop end))]
        ; Otherwise, just cane forward
        [else
         (loop (+ position 1))])))

  ; Get just the targets, remove any external links
  (define (split-link link) (string-split link "|"))
  (define (remove-brackets link) (substring link 2 (- (string-length link) 2)))
  (define (not-external? link) (or (< (string-length link) 4) (not (equal? "http" (substring link 0 4)))))
  (map string-downcase (filter not-external? (map car (map split-link (map remove-brackets links))))))
```

Basically, scan through the file. Anytime we find one of the patterns to remove, find it's close and skip ahead. Anytime we find a link, remember it in the recursion.

At the end, we have a lovely little set of `map`s and `filter`s to clean up the links and remove any potential external links. It's things like this that I miss most when I'm working in non-functional languages...

Anyways, now we have all of the pieces. We can put them all together to get the neighbors for any give page:

```scheme
; Get the neighbors to a given article
(define (get-neighbors title)
  (filter-links (get-first-page-content (get-page title))))
```

And then it's easy enough to solve the problem. I'm actually going to do the general solution first, since we'll have to write it eventually:

```scheme
; Find a path from one page to another, depth first search
(define (find-path from to)
  (set! from (string-downcase from))
  (set! to (string-downcase to))
  (let loop ([page from] [sofar '()])
    (cond
      [(equal? page to) (list to)]
      [(member page sofar) #f]
      [else
       ; Depth first search, try all neighbors
       (let neighbor-loop ([neighbors (get-neighbors page)])
         (cond
           ; Out of neighbors, this page is useless
           [(null? neighbors) #f]
           ; Found a recursive match, build backwards
           [(loop (car neighbors) (cons page sofar))
            => (lambda (next) (cons page next))]
           ; Didn't find a match, try the next neighbor
           [else
            (neighbor-loop (cdr neighbors))]))])))
```

The smartest part of the code here comes in the `neighbor-loop`. Here's where we do the backtracking, primarily by that strange looking `=>` in the second `cond` clause. Basically, that lets you pass the result of the conditional to a function so you can use it without recalculating it. Since anything that's not `#f` in Scheme (and by extension Racket) is true, this means that the recursive cases that don't work and return `#f` will fall through to the `else` case and the rest will call the function with the recursive result as `next`. Hope that explanation made some sort of sense, it's a really helpful tool.

And just for the sake of completeness, here's how we get to Philosophy:

```scheme
; Starting at a given page and taking the first link, how long to Philosophy?
(define (->philosophy start) (find-path start "philosophy"))
```

So how does it actually work in practice?

```scheme
> (->philosophy "Molecule")
'("molecule"
  "atom"
  "matter"
  "rest mass"
  "invariant mass"
  "energy"
  "kinetic energy"
  "physics"
  "natural philosophy"
  "philosophy")
```

I've got an extra link (rest mass) than the source example, but that's mostly because it's a redirect page. My code will print those out, but the sample apparently does not. But overall, it works out pretty well. Let's try something perhaps a bit more amusing:

```scheme
> (->philosophy "Wombat")
'("wombat"
  "quadruped"
  "quadrupedalism"
  "terrestrial locomotion in animals"
  "terrestrial locomotion"
  "evolution"
  "heredity"
  "phenotypic trait"
  "phenotypic character"
  "phenotype"
  "organism"
  "biology"
  "natural science"
  "science"
  "knowledge"
  "fact"
  "proof (truth)"
  "necessity and sufficiency"
  "logic"
  "reason"
  "consciousness"
  "subjectivity"
  "philosophy")
```

And finally the other example from the original daily programmer challenge:

```scheme
> (find-path "asperger syndrome" "logic")
'("asperger syndrome"
  "autism spectrum"
  "pervasive developmental disorder"
  "specific developmental disorder"
  "socialization"
  "sociology"
  "society"
  "interpersonal relationship"
  "inference"
  "formal proof"
  "proposition (philosophy)"
  "proposition"
  "philosophy"
  "reality"
  "being"
  "objectivity (philosophy)"
  "truth"
  "fact"
  "proof (truth)"
  "necessity and sufficiency"
  "logic")
```

The path is a bit different (and longer) than the one given, diverging after *pervasive developmental disorder*. They went to *mental disorder* while I went to *specific developmental disorder*. That's just the nature of Wikipedia. From time to time, people will actually discover the 'paths to philosophy' challenge and purposely switch about links so that it specifically either works faster / doesn't work, but such changes generally get reverted fairly quickly. It's really kind of amazing how Wikipedia has grown to deal with things like that.

In case you were curious, here are the timing differences when using the cache and when not:

```scheme
> (time (->philosophy "Molecule"))
cpu time: 1529 real time: 4018 gc time: 327
...
> (time (->philosophy "Molecule"))
cpu time: 1186 real time: 1269 gc time: 280
...
```

It's really not much faster. Most of the time is spent processing the text and looking for links, perhaps only 1/4 to 1/3 is network latency. But still, if you're doing a lot of testing, that saved bandwidth to Wikipedia is probably worth a few fractions of a penny at the very least. :smile:

And... that's it. Good to go. Here's the code on GitHub if you'd like to see it all in one place: <a title="GitHub: Path to philosophy source" href="https://github.com/jpverkamp/small-projects/blob/master/blog/path-to-philosophy.rkt">path to philosophy source</a>
