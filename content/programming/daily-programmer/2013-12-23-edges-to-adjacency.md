---
title: Edges to adjacency
date: 2013-12-23 14:00:02
programming/languages:
- Racket
- Scheme
programming/sources:
- Daily Programmer
programming/topics:
- Data Structures
- Graph Theory
- Graphs
---
Another quick one, this time <a href="http://www.reddit.com/r/dailyprogrammer/comments/1t6dlf/121813_challenge_140_intermediate_adjacency_matrix/">from /r/dailyprogrammer</a>:

> Your goal is to write a program that takes in a list of edge-node relationships, and print a directed adjacency matrix for it. Our convention will follow that rows point to columns. Follow the examples for clarification of this convention.

<!--more-->

Here's an example:

<table class="table table-striped"><tr><td>
### Input

```
5 5
0 -> 1
1 -> 2
2 -> 4
3 -> 4
0 -> 3
```

</td><td>
### Output

```
01010
00100
00001
00001
00000
```

</td></tr><table class="table table-striped">

Technically, we want it to be a little more general (in that each edge row can have multiple inputs or multiple outputs), but that's easy enough. 

First, we need some sort of structure for storing the graph. I'm going to go ahead and store it internally as the same edge list that we're given (and derive the adjacency matrix on the fly), but I'm going to use hashes to do so. Specifically, hashes to sets:

```scheme
; hashset adt, a hash with sets for values

(define (hashset-add! hash key val)
  (hash-set! hash key (set-add (hash-ref hash key (set)) val)))

(define (hashset-has? hash key val)
  (set-member? (hash-ref hash key (set)) val))
```

This way, we'll hash `node -> (SetOf node)`. Also, we'll want one more helper to parse number lists. So if we see something like `"2 3"`, turn it into `(2 3)`. Something like this:

```scheme
; Convert a string containing a list of nubmers into those numbers
(define (number-string->list str)
  (map string->number (string-split (string-trim str))))
```

Next, we'll solve the actual problem. Basically, we have three steps to accomplish:


* Read the header information: number of nodes and number of lines of input
* Read the edges, sticking them into the hash we mentioned earlier
* Loop through the adjacency matrix, checking the hash if the edge should exist or not


Let's do it:

```scheme
; Given a properly formatted list of edges, print an adjaceny matrix
(define (adjacency [in/str (current-input-port)])
  ; Read from either a string or a port
  (define in (if (string? in/str) (open-input-string in/str) in/str))

  ; Read header: <n = number of nodes> <m = number of lines defining edges>
  (define node-count (read in))
  (define line-count (read in))

  ; Read edges, each line is: <edge start>+ "->" <edge end> "\n"
  ; Skip empty lines
  (define edges (make-hash))
  (for ([line (in-lines in)] #:when (not (equal? "" (string-trim line))))
    (define parts (string-split line "->"))
    ; Add all edges, there can be one or more of both from or to nodes
    (for* ([from (in-list (number-string->list (first parts)))]
           [to   (in-list (number-string->list (second parts)))])
      (hashset-add! edges from to)))

  ; Print out the adjacency matrix 
  (for ([i (in-range node-count)])
    (for ([j (in-range node-count)])
      (display (if (hashset-has? edges i j) 1 0)))
    (newline)))
```

Looks pretty straight forward. Let's run the test given in the example above: 

```scheme
> (adjacency "5 4
0 -> 1 3
1 -> 2
2 -> 4
3 -> 4
")
01010
00100
00001
00001
00000
```

Looks pretty good. To be a little more careful, we can use the `rackunit` as I have before to automatically test our code any time we make any changes (no matter how unlikely):

```scheme
(module+ test
  (require rackunit)

  (define in
    "5 4
0 -> 1 3
1 -> 2
2 -> 4
3 -> 4
")
  (define out 
    "01010
00100
00001
00001
00000
")

  (check-equal? 
   (with-output-to-string (thunk (adjacency in)))
   out))
```

Run with tests... passed. Of course.

And that's all there is to it. It's a neat little puzzle, although the part I personally found most interesting / useful was working out the hashset ADT. I've used it fairly often before. Perhaps I should make a little additional datatype library for these sorts of things... 

In any case, here's the complete source code all in one place: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/adjacency.rkt">adjacency</a>. Enjoy!