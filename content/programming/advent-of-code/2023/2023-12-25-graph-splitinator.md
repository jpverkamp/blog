---
title: "AoC 2023 Day 25: Graph Splitinator"
date: 2023-12-25 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 25: Snowverload](https://adventofcode.com/2023/day/25)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day25) for today (spoilers!)

{{<toc>}}

## Part 1

> Given an [[wiki:undirected graph]](), find 3 edges that split the graph into two [[wiki:connected components]](). Return the product of the component's sizes. 

<!--more-->

### Parsing

I'm just going to `nom` straight into `petgraph` this time:

```rust
fn label(input: &str) -> IResult<&str, &str> {
    alpha1(input)
}

fn edges(input: &str) -> IResult<&str, (&str, Vec<&str>)> {
    separated_pair(
        label,
        terminated(complete::char(':'), space0),
        separated_list1(space1, label),
    )(input)
}

pub fn read(input: &str) -> UnGraph<&str, ()> {
    let (s, lines) = separated_list1(line_ending, edges)(input).unwrap();
    assert!(s.trim().is_empty());

    let mut graph = UnGraph::new_undirected();
    let mut nodes = FxHashMap::default();
    let mut edges = Vec::new();

    for (label, targets) in lines {
        if !nodes.contains_key(label) {
            nodes.insert(label, graph.add_node(label));
        }
        
        for target in targets { 
            if !nodes.contains_key(target) {
                nodes.insert(target, graph.add_node(target));
            }

            graph.add_edge(nodes[label], nodes[target], ());
            edges.push((label, target));
        }
    }

    graph
}
```

### Solution 1: Brute Force

Okay, let's just try removing each set of edges!

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let graph = parse::read(&input);

    let result = (0..3)
        .map(|_i| graph.edge_indices())
        .multi_cartesian_product()
        .filter(|edges| edges.iter().unique().count() == 3)
        .find_map(|edges| {
            let mut graph2 = graph.clone();
            for edge in edges {
                graph2.remove_edge(edge);
            }

            if connected_components(&graph2) != 2 {
                return None;
            }

            let mut dfs = Dfs::new(&graph2, graph.node_indices().next().unwrap());
            let mut count = 0;
            while let Some(_) = dfs.next(&graph2) {
                count += 1;
            }
            Some(count * (graph.node_count() - count))
        })
        .unwrap();

    
    println!("{:?}", result);

    Ok(())
}
```

Well. That's a lot of edges. I bet we can do better.

### A dot graph

[Graphviz]() go!

```rust
fs::write("graph.dot", format!("{:?}", Dot::new(&graph)))?;
```

{{<figure src="/embeds/2023/aoc23-25.png">}}

Yeah... that's kind of impossible to look at. But if you open it up in a new tab and scroll around, you'll see there are two halves with an obvious three lines between them!

Now if only you could find them...

### Solution 2: Calculate 'heavy' edges

I expect this is a known algorithm, but my basic idea is:

* For each node, calculate the [[wiki:a-star]]() path to every other node
  * For each edge in that path, add to a global counter

The idea is that halfish of these paths are going to go over the same three edges. 

Now, instead of just iterating over edges in the order originally specified, use this new order:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let graph = parse::read(&input);

    // Count how many times we cross each edge
    let mut counter: FxHashMap<_, usize> = FxHashMap::default();

    // For each pair of nodes, find the shortest path between them
    // Add each edge in that path to the counter
    graph
        .node_indices()
        .take(10)
        .cartesian_product(graph.node_indices())
        .for_each(|(a, b)|
            astar(
                &graph, 
                a, |node| node == b,
                |_| 1,
                |_| 0
            )
            .unwrap()
            .1
            .iter()
            .tuple_windows()
            .map(|(a, b)| graph.find_edge(*a, *b).unwrap())
            .for_each(|edge| 
                *counter.entry(edge).or_default() += 1
            )
        );
        
    // Sort the list of edges with the heaviest first
    let heavy_edges = counter
        .iter()
        .sorted_by(|(_, a), (_, b)| b.cmp(a))
        .map(|(edge, _)| *edge)
        .collect_vec();

    // Try each combination of 3 edges, starting with the 'heaviest'
    // As soon as we find a trio that splits the graph in 2 we have an answer
    let result = (0..3)
        .map(|_i| heavy_edges.iter())
        .multi_cartesian_product()
        .filter(|edges| edges.iter().unique().count() == 3)
        .find_map(|edges| {
            let mut graph2 = graph.clone();
            for edge in edges {
                graph2.remove_edge(*edge);
            }

            if connected_components(&graph2) != 2 {
                return None;
            }

            let mut dfs = Dfs::new(&graph2, graph.node_indices().next().unwrap());
            let mut count = 0;
            while let Some(_) = dfs.next(&graph2) {
                count += 1;
            }
            Some(count * (graph.node_count() - count))
        })
        .unwrap();
   
    println!("{result}");
    Ok(())
}
```

And... in about 2 seconds we have an answer. 

### A better N

You'll note with that `take(10)` there that we're only starting at 10 of the nodes. There's no reason to do the whole thing. 

What's the best value of N? 

```rust
for n in 1..=graph.node_count() {
    let start = std::time::Instant::now();
    
    // Count how many times we cross each edge
    let mut counter: FxHashMap<_, usize> = FxHashMap::default();

    // For each pair of nodes, find the shortest path between them
    // Add each edge in that path to the counter
    graph
        .node_indices()
        .take(n)
        // ...


    println!("{}: {:?}", n, start.elapsed());
}
```

It's... very slow to solve this so many times, but we find out:

```bash
$ just run 25 1-best-n

cat data/$(printf "%02d" 25).txt | cargo run --release -p day$(printf "%02d" 25) --bin part1-best-n
   Compiling day25 v0.1.0 (/Users/jp/Projects/advent-of-code/2023/solutions/day25)
    Finished release [optimized] target(s) in 0.31s
     Running `target/release/part1-best-n`
1: 194.379984917s
2: 47.260634583s
3: 546.839292ms
4: 724.617042ms
5: 996.805583ms
6: 1.0664215s
7: 1.251643125s
8: 1.394995458s
9: 1.559387833s
10: 1.724106666s
...
```

Turns out the best N is... `3` (note: ms, not seconds). So we'll use that!

### Performance

```bash
$ just time 25 1

hyperfine --warmup 3 'just run 25 1'
Benchmark 1: just run 25 1
  Time (mean ± σ):     679.8 ms ±  18.5 ms    [User: 573.2 ms, System: 16.8 ms]
  Range (min … max):   664.6 ms … 716.5 ms    10 runs
```

Nice!

## Part 2

> There's never a part 2. :smile:

Merry Christmas!
