---
title: Graph radius
date: 2014-01-14 14:00:41
programming/languages:
- Racket
- Scheme
programming/topics:
- Data Structures
- Graph Theory
- Graphs
- Mathematics
---
[Here's](http://www.reddit.com/r/dailyprogrammer/comments/1tiz4z/122313_challenge_140_intermediate_graph_radius/) a quick problem from the DailyProgrammer subreddit. Basically, we want to calculate the radius of a graph:

> {{< inline-latex "radius(g) = \min\limits_{n_0 \in g} \max\limits_{n_1 \in g} d_g(n_0, n_1)" >}}

<!--more-->

To make that a little less mathematical, we're trying to find the minimum distance it would take to get from one chosen graph to any other[^1]. Perhaps an example, the Butterfly graph:

<img alt="" src="https://upload.wikimedia.org/wikipedia/commons/f/f9/Butterfly_graph.svg" class="alignnone" width="227" height="107" />
<small>[[wiki:source|File:Butterfly graph.svg]]()</small>

If you consider the node in the top left, you can get to the bottom left or center in 1 unit or either right side in 2. That means that node has an *eccentricity* of 2. But the center node can get to any other in only 1. So it's eccentricity is 1. Since that's the lowest, the radius of the Butterfly graph is 1.

How do we turn that into code though?

Well, originally I started out to write a graph library for Racket. It was actually pretty neat, using the {{< doc racket "define-generics" >}} form so that we could have a few different kinds of graphs.

Then, I actually took a chance and looked at Racket's [pkg system](http://pkg.racket-lang.org/)... and there it was: [github:stchang/graph](https://github.com/stchang/graph/tree/master). It's pretty much exactly what I would have done[^2], so why reinvent the wheel? Here's the documentation: [graph documentation](http://stchang.github.io/graph/graph.html)

So, first we need a distance function. It's a bit funny looking, but hopefully, it's relatively straight forward:

```scheme
; Calculate the distance between n0 and n1 in the graph g
(define (distance g n0 n1)
  ; Start with 0 units to the origin
  (let loop ([distances (hash n0 0)])
    (cond
      ; If we ever have a distance to the target, just return that directly
      [(hash-ref distances n1 #f) => identity]
      ; Otherwise, try to extend each node already in the graph
      ; It would be more efficient to only expand each node once, but so it goes
      [else
       (define next-distances (hash-copy distances))
       (for* ([(node distance) (in-hash distances)]
              [neighbor (in-neighbors g node)]
              #:unless (hash-has-key? distances neighbor))
         (hash-set! next-distances neighbor (+ distance 1)))

       ; If we have any new nodes, keep looking; otherwise we aren't connected
       (if (= (hash-count distances) (hash-count next-distances))
           #f
           (loop next-distances))])))
```

Basically, we set up a hash of distances and then recursively fill it in. If we've already set a node, that means there is no shorter way to get there. If we ever get to the target, we've found a distance, so we'll use the `=>` form of the `cond` to pass the `hash-ref`'ed value to `identity` (which just returns it).

If that doesn't work, we hit an expansion phase. Originally, this directly modified the hash, but this caused issues with the iteration, so I create a copy and modify that one instead. Then we check if we actually made a change. If we didn't expand the distance graph, we never will. Otherwise, we keep looking.

With that, we have enough to define the eccentricity function defined above (also known as {{< inline-latex "\epsilon" >}}):

{{< latex >}}\epsilon_g(n_0) = \max\limits_{n_1 \in g} d(n_0, n_1){{< /latex >}}

```scheme
; The eccentricity of a node is the distance to the furthest other node
(define (eccentricity g n)
  (apply max (map (curry distance g n) (in-vertices g))))
```

From inside to out, `in-vertices` returns a list of vertices (rather than a sequence as the name might suggest). `(curry distance g n)` creates a function of the form `(λ (x) (distance g n x))`, which we them map across the vertices to get a list of distances. If we don't actually have a connected graph, that will cause issues (since `distance` will return `#f`), but that's okay. Eccentricity is infinite for those cases anyways.

What's interesting about this though, is that this is exactly the same code for the graph radius. Just loop again and use the eccentricity instead of the distance:

{{< latex >}}radius(g) = \min\limits_{n_0 \in g} \epsilon_g(n_0) = \min\limits_{n_0 \in g} \max\limits_{n_1 \in g} d(n_0, n_1){{< /latex >}}

```scheme
; The radius of a graph is the minimum eccentricity
(define (graph-radius g)
  (apply min (map (curry eccentricity g) (in-vertices g))))
```

While we're at it, the [[wiki:Wikipedia page for graph radius|Distance (graph theory)]]() also mentions a graph's `diameter`:

{{< latex >}}radius(g) = \max\limits_{n_0 \in g} \epsilon_g(n_0) = \max\limits_{n_0 \in g} \max\limits_{n_1 \in g} d(n_0, n_1){{< /latex >}}

```scheme
; The diameter of a graph is maximum eccentricity
(define (graph-diameter g)
  (apply max (map (curry eccentricity g) (in-vertices g))))
```

Let's run it through a whole sequence of tests. Take the three given in the [problem definition](http://www.reddit.com/r/dailyprogrammer/comments/1tiz4z/122313_challenge_140_intermediate_graph_radius/) plus a few more from the comments, we have a pretty good test bed:

```scheme
(module+ test
  (require rackunit)

  (define petersen-graph (read-graph "
10
0 1 0 0 1 1 0 0 0 0
1 0 1 0 0 0 1 0 0 0
0 1 0 1 0 0 0 1 0 0
0 0 1 0 1 0 0 0 1 0
1 0 0 1 0 0 0 0 0 1
1 0 0 0 0 0 0 1 1 0
0 1 0 0 0 0 0 0 1 1
0 0 1 0 0 1 0 0 0 1
0 0 0 1 0 1 1 0 0 0
0 0 0 0 1 0 1 1 0 0
"))
  (check-equal? (graph-radius petersen-graph) 2)
  (check-equal? (graph-diameter petersen-graph) 2)

  (define butterfly-graph (read-graph "
5
0 1 1 0 0
1 0 1 0 0
1 1 0 1 1
0 0 1 0 1
0 0 1 1 0
"))
  (check-equal? (graph-radius butterfly-graph) 1)
  (check-equal? (graph-diameter butterfly-graph) 2)

  (define sample-inputs/outputs (read-graph "
10
0 1 0 0 1 1 0 0 0 0
1 0 1 0 0 0 1 0 0 0
0 1 0 1 0 0 0 1 0 0
0 0 1 0 1 0 0 0 1 0
1 0 0 1 0 0 0 0 0 1
1 0 0 0 0 0 0 1 1 0
0 1 0 0 0 0 0 0 1 1
0 0 1 0 0 1 0 0 0 1
0 0 0 1 0 1 1 0 0 0
0 0 0 0 1 0 1 1 0 0
"))
  (check-equal? (graph-radius sample-inputs/outputs) 2)
  (check-equal? (graph-diameter sample-inputs/outputs) 2)

  (define nauru-graph (read-graph "
24
0 1 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0
1 0 0 1 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0
0 0 0 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1
0 1 1 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 1 0 0 1 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0
1 0 0 0 1 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 1 0 0 0 1 0 0 0 0 0 0 0 1 0 0 0 0
0 0 0 0 0 0 1 0 0 1 0 0 0 1 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 1 1 0 0 0 0 0 0 0 0 0 0 0 1 0
0 0 0 1 0 0 0 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 1 0 0 1 0 0 0 0 1 0 0 0 0 0 0 0
0 0 0 0 0 1 1 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 0 0 0 0 0
0 0 0 0 0 0 0 1 0 0 0 0 1 0 0 1 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 0 0 0 1 0 0 0
0 1 0 0 0 0 0 0 0 0 0 0 0 1 1 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 0 0 1 0 0 0 0 0 0
0 0 0 0 1 0 0 0 0 0 0 0 1 0 0 0 1 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 1
0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 1 0
1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 0 0 0
0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1
0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 0
"))
  (check-equal? (graph-radius nauru-graph) 4)
  (check-equal? (graph-diameter nauru-graph) 4)

  (define desargues-graph (read-graph "
20
0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 1 0 0 0 0
0 0 0 0 0 0 0 0 0 0 1 0 1 0 0 0 1 0 0 0
0 0 0 0 0 0 0 0 0 0 0 1 0 1 0 0 0 1 0 0
0 0 0 0 0 0 0 0 0 0 0 0 1 0 1 0 0 0 1 0
0 0 0 0 0 0 0 0 0 0 1 0 0 1 0 0 0 0 0 1
0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 1 0
0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 1
0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 0 0 0 1
0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 1 1 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 1 1 0 0
0 1 0 0 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0
1 0 1 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0
0 1 0 1 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0
0 0 1 0 1 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0
1 0 0 1 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0
1 0 0 0 0 0 0 1 1 0 0 0 0 0 0 0 0 0 0 0
0 1 0 0 0 0 0 0 1 1 0 0 0 0 0 0 0 0 0 0
0 0 1 0 0 1 0 0 0 1 0 0 0 0 0 0 0 0 0 0
0 0 0 1 0 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 1 0 1 1 0 0 0 0 0 0 0 0 0 0 0 0
"))
  (check-equal? (graph-radius desargues-graph) 5)
  (check-equal? (graph-diameter desargues-graph) 5)

  )
```

100% passed!

If you'd like to see all of the code at once, you can do so here: [graph-radius](https://github.com/jpverkamp/small-projects/blob/master/blog/graph-radius.rkt)

[^1]: Okay, so I'm not great at making it less mathematical...
[^2]: Although I was going for a more functional style / less mutation. So it goes.
