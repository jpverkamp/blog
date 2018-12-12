---
title: "AoC 2018 Day 8: Checksum Treeification"
date: 2018-12-08
programming/languages:
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [The Sum of Its Parts](https://adventofcode.com/2018/day/8)

> **Part 1:** A custom tree data structure is defined as:

> - child count
> - metadata count
> - `child count` additional subtrees (recursive)
> - `metadata count` metadata nodes

> Calculate the sum of all metadata nodes.

<!--more-->

Yay! Something Racket is great at! {{< wikipedia text="Trees" page="Tree (data structure)" >}}!

First, let's read in the structure. Reading recursive data is wonderfully simple in Racket:

```racket
(struct tree (children metadata) #:transparent)

; A tree is count-children, count-metadata, children..., metadata...
(define (read-tree)
  (define child-count (read))
  (define metadata-count (read))
  (tree (for/list ([i (in-range child-count)])
          (read-tree))
        (for/list ([i (in-range metadata-count)])
          (read))))
```

And calculating the sum recursively across a tree is just about as short:

```racket
; Sum all metadata values for a simple checksum
(define (simple-checksum tr)
  (+ (for/sum ([child (in-list (tree-children tr))])
       (simple-checksum child))
     (apply + (tree-metadata tr))))
```

Fun!

> **Part 2:** Now, calculate the sum as follows:

> - If a node has no children, sum the metadata nodes
> - Otherwise, sum the metadata nodes as follows:
>   - If a metadata value is small enough to be a 1-based index of children, use that child's checksum
>   - Otherwise, use 0

> - Calculate the new checksum.

Honestly, it's just as long to describe the algorithm as to make it into code. There's a bit of weird since the data structure is using 1-based indexing (what are we, Lua? Matlab?), but not too bad:

```racket
; Checksum with no children is sum of metadata
; Checksum with children uses the metadata as index, sums those children
(define (complex-checksum tr)
  (cond
    [(null? (tree-children tr))
     (apply + (tree-metadata tr))]
    [else
     (for/sum ([index (in-list (tree-metadata tr))])
       (cond
         [(<= 1 index (length (tree-children tr)))
          (complex-checksum (list-ref (tree-children tr) (sub1 index)))]
         [else
          0]))]))
```

Print them and we go:

```bash
$ cat input.txt | racket checksum-treeificator.rkt

[part 1] 37262
[part 2] 20839
```

I like trees. :smile:
