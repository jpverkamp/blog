---
title: "AoC 2024 Day 23: LAN Partinator"
date: 2024-12-23 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
programming/topics: 
- Graph Theory
- NP Complete
- Recursion
- Memoization
---
## Source: [Day 23: LAN Party](https://adventofcode.com/2024/day/23)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day23.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> You are given the edges of an [[wiki:undirected graph]](). Count how many [[wiki:complete graph|complete]]() [[wiki:subgraphs]]() of size three exist that contain one or more starting with the letter `t`.

Aside: Games with local (but not hotseat) multiplayer have gotten rather rarer over the years... how many people still know what a [[wiki:LAN party]]() is/was? 

<!--more-->

I spent a little while making a `StrGraph<'a>` library for this one. You can see the entire source for that module [here](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/strgraph.rs). Essentially:

* It can read `From<&'a str>`
* Internally, it stores `nodes`, `edges`, and `neighbors` as `HashSets`/`HashMaps`. I store both `edges` and `neighbors` because I needed `edges` first and only later realized it would be nice to have both. 
* Accessors for `nodes`, `edges`, and `neighbors` return `impl Iterator<Item = &' str>` (or a tuple for `edges`)

And the following methods (in the order I wrote them):

* `completely_connected(node: &'a str)` - Returns *a* completely connected subgraph containing `node`
* `largest_completely_connected(node: &'a str)` - Returns the *largest* completely connected subgraph containing `node`; this is super inefficient
* `is_completely_connected(nodes: &[&'a str])` - A helper to check if the given list of nodes is a completely connected component

All that being said, I only used the accessor for `part1`:

```rust
#[aoc(day23, part1, v1)]
fn part1_v1(input: &str) -> usize {
    let g = StrGraph::from(input);
    let mut count = 0;

    let mut sorted_nodes = g.nodes().collect::<Vec<_>>();
    sorted_nodes.sort();

    for (i, a) in sorted_nodes.iter().enumerate() {
        for (j, b) in sorted_nodes.iter().skip(i + 1).enumerate() {
            if !g.has_edge(a, b) {
                continue;
            }

            for c in sorted_nodes.iter().skip(i + j + 1) {
                if !g.has_edge(a, c) || !g.has_edge(b, c) {
                    continue;
                }

                if a.starts_with('t') || b.starts_with('t') || c.starts_with('t') {
                    count += 1;
                }
            }
        }
    }

    count
}
```

It really does just look for an `a`, `b`, and `c` that are connected and have one starting with `t`. THere is a slight improvement in that it guarantees that `i < j < k` so we only count each ordering once and also doesn't bother searching for `c` if `a` and `b` are already not connected. 

```bash
$ cargo aoc --day 23 --part 1

AOC 2024
Day 23 - Part 1 - v1 : 1467
	generator: 3.166µs,
	runner: 26.880625ms
```

Woot. 

Why did I sort the nodes first? To guarantee a consistent ordering. For this problem, it doesn't matter... 

## Part 2

> Find the largest complete subgraph. Print the nodes [[wiki:lexicographically]]() sorted, comma delimited. 

There we go. 

Okay, first attempt essentially uses 

```rust
#[aoc(day23, part2, sorted_complete)]
fn part2_sorted_complete(input: &str) -> String {
    let g = StrGraph::from(input);
    let mut checked = HashSet::new();

    // NOTE: This would not actually work in general

    g.nodes()
        .sorted() // This at least guarantees we'll get the same ordering
        .filter_map(|n| {
            if checked.contains(n) {
                None
            } else {
                let component = g.completely_connected(n);
                for &n in component.iter() {
                    checked.insert(n);
                }
                Some(component)
            }
        })
        .max_by(|a, b| a.len().cmp(&b.len()))
        .map(|c| c.iter().sorted().join(","))
        .unwrap()
}
```

With `completely_connected` being:

```rust
impl<'a> StrGraph<'a> {
    // This will return *a* completely connected component for a node
    pub fn completely_connected(&self, node: &'a str) -> HashSet<&'a str> {
        let mut connected = HashSet::new();
        connected.insert(node);

        // For each node, add it if it's connected to all other added nodes
        for &n in self.nodes.iter().sorted() {
            if !connected.iter().all(|&c| self.has_edge(n, c)) {
                continue;
            }

            connected.insert(n);
        }

        connected
    }
}
```

In order to make sure that this function doesn't work sometimes but not others, I do again make sure that we're working on a sorted list (both in the `part2*` function and in `completely_connected`). Being able to do that inline in an `iter` is a function of {{<crate itertools>}}. 

Basically, we go through each node, getting *a* complete subgraph it's connected to. These are then not checked again, plus we keep the longest of these. `c.iter().sorted().join(",")` is a delightful way to get a sorted, comma delimited list of nodes. 

So...

```bash
$ cargo aoc --day 23 --part 2

AOC 2024
Day 23 - Part 2 - most_connected : di,gs,jw,kz,md,nc,qp,rp,sa,ss,uk,xk,yn
	generator: 17.666µs,
	runner: 3.456209ms
```

This is technically the correct answer. But we actually got lucky with that. Alphabetical ordering of nodes *happens* to create this connected node when scanning through. 

Basically, if we have something like this:

```text
    D
    |
    C
   / \
A-B---F-E
```

Assume our HashSet returns things in alphabetical order (as a worst case):

1. We'll start with `A`, get `A,B`; so we'll skip `B`
2. Then we'll do `D`, get `C,D`; so we'll skip `D`
3. Then we'll do `E`, get `E,F`; so we'll skip `F`

We never return the component `B,C,F`, which is what we actually want. 

Even removing the checked.contains doesn't actually fix this, in the worst case. Since if we get an ordering such that `A` and `B` return `A,B` and `C` and `D` return `C,D`; etc.

We'll still never see the component `B,C,F`.

Here's a test showing that:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    // Constructed to fail part2_largest_complete
    // See the comment in that function
    //
    //     D
    //     |
    //     C
    //    / \
    // A-B---F-E
    const EXAMPLE2: &str = "\
a-b
b-c
c-d
c-f
f-e
b-f";

    // This is constructed to fail due to the ordering of the graph
    #[test]
    #[ignore]
    fn test_part2_largest_complete_example2() {
        assert_eq!(part2_largest_complete(EXAMPLE2), "b,c,f");
    }
}
```

What we need is completely_connected to return the *largest* component for a node. But this is *significantly* more expensive.

### Corrected version 1: Largest completely connected

Okay, so we found the answer, but there's no guarantee that if our input will return the correct answer. What does it need to actually guarantee that? Well:

```rust
impl<'a> StrGraph<'a> {
        // This will return the *largest* completely connected component for a node
    pub fn largest_completely_connected(&self, node: &'a str) -> HashSet<&'a str> {
        fn recur<'a>(
            nodes: &HashSet<&'a str>,
            neighbors: &HashMap<&'a str, HashSet<&'a str>>,
            component: Vec<&'a str>,
        ) -> Vec<&'a str> {
            nodes
                .iter()
                // Don't check nodes we've already done
                .filter(|&n| !component.contains(n))
                // Check if all neighbors are in the component
                .filter(|&n| {
                    component
                        .iter()
                        .all(|&c| neighbors.get(n).unwrap().contains(c))
                })
                // Recur adding that component
                .map(|n| {
                    recur(nodes, neighbors, {
                        let mut component = component.clone();
                        component.push(n);
                        component
                    })
                })
                // Which is the largest
                .max_by(|a, b| a.len().cmp(&b.len()))
                // If we didn't find a larger child, return all
                .unwrap_or_else(|| component.to_vec())
        }

        recur(&self.nodes, &self.neighbors, vec![node])
            .into_iter()
            .collect()
    }
}
```

The obvious (to me) at least way of doing this is to start at the given node, then write a recursive function that will try adding each neighbor, one at a time. Any time we have no more neighbors that are connected to all previous nodes, return the component. As we're unwinding, we only keep the largest branch. 

```rust
#[aoc(day23, part2, largest_complete)]
fn part2_largest_complete(input: &str) -> String {
    let g = StrGraph::from(input);
    let mut checked = HashSet::new();

    // The 'significantly more expensive' version

    g.nodes()
        .filter_map(|n| {
            if checked.contains(n) {
                None
            } else {
                let component = g.largest_completely_connected(n);
                for &n in component.iter() {
                    checked.insert(n);
                }
                Some(component)
            }
        })
        .max_by(|a, b| a.len().cmp(&b.len()))
        .map(|c| c.iter().sorted().join(","))
        .unwrap()
}
```

This does technically work (on both given example graphs), but man is it slow. I let it run an hour and still no progress. It turns out this problem is [[wiki: NP-complete]]() and running it on 3000+ nodes is *slow*. 

### Corrected version 2: Recursion + memoization

Just out of curiosity, I did take the observation that since it's a recursive problem, we should be able to cut off a lot of branches with memoization:

```rust
#[aoc(day23, part2, recur_memo)]
fn part2_recur_memo(input: &str) -> String {
    let graph = StrGraph::from(input);

    fn largest_completely_connected_subgraph<'a>(
        graph: &StrGraph,
        cache: &mut HashMap<Vec<&'a str>, Vec<&'a str>>,
        nodes: Vec<&'a str>,
    ) -> Vec<&'a str> {
        // We've already cached this result
        if let Some(result) = cache.get(&nodes) {
            return result.clone();
        }

        // Check if we're already completely connected
        if graph.is_completely_connected(&nodes) {
            cache.insert(nodes.clone(), nodes.clone());
            return nodes;
        }

        // Otherwise, for each node, try removing it and recurring
        let mut largest: Option<Vec<&'a str>> = None;
        for (i, _) in nodes.iter().enumerate() {
            let mut new_nodes = nodes.clone();
            new_nodes.remove(i);
            let result = largest_completely_connected_subgraph(graph, cache, new_nodes);

            if largest.is_none() || result.len() > largest.as_ref().unwrap().len() {
                largest = Some(result);
            }
        }
        let largest = largest.unwrap();

        cache.insert(nodes, largest.clone());
        largest
    }

    let nodes = graph.nodes().sorted().collect::<Vec<_>>();
    let mut cache = HashMap::new();

    largest_completely_connected_subgraph(&graph, &mut cache, nodes)
        .iter()
        .sorted()
        .join(",")
}
```

This sort of works the other way around. It starts with the entire graph, then one at a time, tries removing nodes and recurring. As soon as we have a complete subgraph, we're done. Then cache each of those subgraphs.

The problem is... this can't possibly be efficient, again because of the whole NP-complete thing. 

It does work perfectly well on my smaller examples and I assume it would be fine for my input... but again, I didn't let it finish. 

### Corrected version 3: Ordering by most connected nodes

Okay, last but not least, we can actually use the structure of our input while at the same time guaranteeing that we'll eventually find an answer even in the worst case. 

Here's some quick Python:

```python
import collections, sys

neighbors = collections.Counter()

for line in sys.stdin:
    (a, b) = line.strip().split("-")
    neighbors[a] += 1
    neighbors[b] += 1

by_count = collections.defaultdict(set)
for node, count in neighbors.items():
    by_count[count].add(node)

for count in sorted(by_count.keys(), reverse=True):
    nodes = ",".join(sorted(node for node in by_count[count]))
    print(f"{count}: {nodes}")
```

Which outputs:

```text
13: aa,ab,ac,ad,af,ag,ah,ai,ak,al,am,an,ao,aq,ar,as,at,au,av,aw,ay,az,ba,bb,bc,bg,bh,bi,bj,bm,bo,bp,br,bt,bu,bv,bw,bx,by,bz,cd,cf,cg,ch,ci,cj,ck,cl,cm,co,cp,cq,cr,cs,ct,cu,cv,cw,cx,cy,cz,dd,de,df,dg,dh,di,dj,dk,dl,dm,do,dp,dr,ds,dt,dv,dw,dx,ea,eb,ec,ed,ee,ef,eh,ei,ep,er,es,et,ev,ew,ex,ey,fb,fc,fe,fg,fh,fj,fk,fl,fm,fn,fo,fq,fr,fs,ft,fu,fv,fw,fx,fy,ga,gb,gc,ge,gf,gg,gh,gi,gj,gk,gm,gn,gp,gq,gr,gs,gt,gu,gv,gw,gx,gy,gz,hc,he,hj,hk,hn,ho,hp,hq,hr,ht,hv,hw,hx,hy,hz,ia,ib,ie,if,ig,ih,ii,ij,il,im,in,io,ip,iq,ir,it,iu,iv,iw,ix,iy,iz,ja,jb,jc,jd,jg,jh,jk,jl,jm,jo,jp,jq,jr,js,ju,jv,jw,jx,jz,ka,kc,kd,kf,kg,kh,ki,kk,kn,ko,kp,kq,kr,kt,ku,kv,kx,ky,kz,la,lb,lc,ld,le,lf,lg,lh,ll,lm,ln,lo,lp,lq,lr,lt,lu,lw,lx,ly,lz,ma,mb,mc,md,me,mf,mg,mi,mj,mk,ml,mn,mo,mq,mr,ms,mt,mu,mw,my,mz,na,nb,nc,nf,ng,nh,ni,nk,nl,nm,nn,no,np,nr,ns,nt,nu,nw,nx,ny,nz,oa,oc,od,oe,of,og,oj,ok,ol,oo,op,oq,or,ot,ou,ov,ow,ox,oy,oz,pa,pb,pc,pd,pe,pg,ph,pj,pl,pm,pn,po,pp,pq,pr,pt,pu,pv,pw,px,py,pz,qb,qc,qf,qg,qi,qj,qk,ql,qm,qo,qp,qq,qr,qs,qt,qu,qv,qw,qy,ra,rd,re,rg,rh,ri,rj,rl,rm,rn,ro,rp,rq,rs,ru,rv,rw,ry,sa,sb,sd,se,sf,sg,sh,si,sj,sk,sl,sn,so,sq,sr,ss,st,su,sw,sy,sz,ta,tb,tc,td,te,tf,tg,th,ti,tj,tk,tl,tm,to,tp,tq,tr,ts,tt,tu,tv,tw,tx,ty,ua,uc,ud,ue,uf,ug,uh,ui,uk,ul,um,uo,up,uq,ur,us,uw,ux,uy,uz,va,vb,vd,ve,vf,vi,vj,vk,vl,vm,vn,vo,vp,vq,vr,vs,vu,vw,vx,vy,vz,wa,wd,we,wf,wg,wj,wk,wl,wm,wn,wo,wp,wr,ws,wv,ww,wx,wy,wz,xb,xd,xe,xf,xg,xh,xk,xl,xn,xo,xp,xq,xr,xs,xt,xu,xv,xx,xy,yb,yd,ye,yf,yg,yh,yi,yj,yl,yn,yo,yp,yq,yr,ys,yt,yu,yv,yw,yx,yy,yz,za,zc,ze,zf,zg,zi,zj,zk,zl,zm,zn,zo,zq,zr,zs,zt,zu,zw,zx
```

... 

So every single node in the graph is connected to exactly 13 others. That does *heavily* imply that our largest connected subgraph is going to have 12 nodes (even if we didn't already know that). 

I ended up writing a solution from that that's still a bit more general:

```rust
#[aoc(day23, part2, most_connected)]
fn part2_most_connected(input: &str) -> String {
    let graph = StrGraph::from(input);

    // Order nodes by descending number of neighbors
    // For each, check if removing any single neighbor is connected
    // Any nodes with higher order than the connected component will be checked first
    // But due to the structure of our graph, this way is efficient
    graph
        .nodes()
        .map(|node| (node, graph.neighbors(node).count()))
        .sorted_by(|a, b| a.1.cmp(&b.1))
        .rev()
        .find_map(|(node, _)| {
            let neighbors = graph.neighbors(node).collect::<Vec<_>>();

            // Try removing each single neighbor
            for neighbor in neighbors.iter() {
                let mut neighbors_without = neighbors.clone();
                neighbors_without.retain(|&n| n != *neighbor);

                if graph.is_completely_connected(&neighbors_without) {
                    neighbors_without.push(node);
                    return Some(neighbors_without.iter().sorted().join(","));
                }
            }

            // If we made it here, we couldn't find a solution removing more than 1 neighbor
            None
        })
        .unwrap()
}
```

As noted, it's going to go through the nodes in descending order of number of neighbors (when I wrote this, I didn't realize that they were all 13 yet... :smile:). For each node, it will take the list of neighbors (guaranteed all connected to that node), and try removing them each one at a time. As soon as we find a complete subgraph, return (`find_map`). 

This works specifically on any graph that has the structure of a bunch of complete subgraphs (of any size really), where any node in the graph has exactly *1* connection outside of that complete subgraph. If all of the nodes in it have more than one connect, this will fail. 

But for our specific input (and I assume any generated the same way), it works great!

```bash
$ cargo aoc --day 23 --part 2

AOC 2024
Day 23 - Part 2 - sorted_complete : di,gs,jw,kz,md,nc,qp,rp,sa,ss,uk,xk,yn
	generator: 16.666µs,
	runner: 9.681875ms

Day 23 - Part 2 - most_connected : di,gs,jw,kz,md,nc,qp,rp,sa,ss,uk,xk,yn
	generator: 17.666µs,
	runner: 3.456209ms
```

Better even than the sorted case, and 'slightly' more guaranteed to return a correct answer? 

### This is stupid...

Because I would be remiss if I didn't mention it:

```rust
#[aoc(day23, part2, nested_loops)]
fn part2_nested_loops(input: &str) -> String {
    let graph = StrGraph::from(input);

    let nodes = graph.nodes().sorted().collect::<Vec<_>>();

    for (i0, n0) in nodes.iter().enumerate() {
        for (i1, n1) in nodes.iter().enumerate().skip(i0 + 1) {
            if [n0].iter().any(|&n| !graph.has_edge(n, n1)) {
                continue;
            }

            for (i2, n2) in nodes.iter().enumerate().skip(i1 + 1) {
                if [n0, n1].iter().any(|&n| !graph.has_edge(n, n2)) {
                    continue;
                }

                for (i3, n3) in nodes.iter().enumerate().skip(i2 + 1) {
                    if [n0, n1, n2].iter().any(|&n| !graph.has_edge(n, n3)) {
                        continue;
                    }

                    for (i4, n4) in nodes.iter().enumerate().skip(i3 + 1) {
                        if [n0, n1, n2, n3].iter().any(|&n| !graph.has_edge(n, n4)) {
                            continue;
                        }

                        for (i5, n5) in nodes.iter().enumerate().skip(i4 + 1) {
                            if [n0, n1, n2, n3, n4].iter().any(|&n| !graph.has_edge(n, n5)) {
                                continue;
                            }

                            for (i6, n6) in nodes.iter().enumerate().skip(i5 + 1) {
                                if [n0, n1, n2, n3, n4, n5].iter().any(|&n| !graph.has_edge(n, n6)) {
                                    continue;
                                }

                                for (i7, n7) in nodes.iter().enumerate().skip(i6 + 1) {
                                    if [n0, n1, n2, n3, n4, n5, n6].iter().any(|&n| !graph.has_edge(n, n7)) {
                                        continue;
                                    }

                                    for (i8, n8) in nodes.iter().enumerate().skip(i7 + 1) {
                                        if [n0, n1, n2, n3, n4, n5, n6, n7].iter().any(|&n| !graph.has_edge(n, n8)) {
                                            continue;
                                        }

                                        for (i9, n9) in nodes.iter().enumerate().skip(i8 + 1) {
                                            if [n0, n1, n2, n3, n4, n5, n6, n7, n8].iter().any(|&n| !graph.has_edge(n, n9)) {
                                                continue;
                                            }

                                            for (i10, n10) in nodes.iter().enumerate().skip(i9 + 1) {
                                                if [n0, n1, n2, n3, n4, n5, n6, n7, n8, n9].iter().any(|&n| !graph.has_edge(n, n10)) {
                                                    continue;
                                                }

                                                for (i11, n11) in nodes.iter().enumerate().skip(i10 + 1) {
                                                    if [n0, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10].iter().any(|&n| !graph.has_edge(n, n11)) {
                                                        continue;
                                                    }

                                                    for (_, n12) in nodes.iter().enumerate().skip(i11 + 1) {
                                                        if [n0, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11].iter().any(|&n| !graph.has_edge(n, n12)) {
                                                            continue;
                                                        }

                                                        return [n0, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12]
                                                            .iter()
                                                            .sorted()
                                                            .join(",");
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    unreachable!("No solution");
}
```

...

```bash
$ cargo aoc --day 23 --part 2

AOC 2024
Day 23 - Part 2 - sorted_complete : di,gs,jw,kz,md,nc,qp,rp,sa,ss,uk,xk,yn
	generator: 16.666µs,
	runner: 9.681875ms

Day 23 - Part 2 - most_connected : di,gs,jw,kz,md,nc,qp,rp,sa,ss,uk,xk,yn
	generator: 17.666µs,
	runner: 3.456209ms

Day 23 - Part 2 - nested_loops : di,gs,jw,kz,md,nc,qp,rp,sa,ss,uk,xk,yn
	generator: 1.084µs,
	runner: 167.462333ms
```

It's slower and stupider... but it works?

### ...and complicated

I have to.

```rust
#[aoc(day23, part2, nested_loops_macro)]
fn part2_nested_loops_macro(input: &str) -> String {
    let graph = StrGraph::from(input);
    let nodes = graph.nodes().sorted().collect::<Vec<_>>();

    macro_rules! wtf {
        // First case / outermost loop, starts the recursion
        ($i:ident $n:ident $($rest_i:ident $rest_n:ident)*) => {
            for ($i, $n) in nodes.iter().enumerate() {
                wtf!($($rest_i $rest_n)* => $i $n);
            }
        };

        // Base case / innermost loop, finally does the return
        ($last_i:ident $last_n:ident => $prev_i:ident $($prev_n:ident),*) => {
            for (_, $last_n) in nodes.iter().enumerate().skip($prev_i + 1) {
                if [$($prev_n),*].iter().any(|&n| !graph.has_edge(n, $last_n)) {
                    continue;
                }

                return [$($prev_n),*, $last_n]
                    .iter()
                    .sorted()
                    .join(",");
            }
        };

        // Intermediate cases, continues the recursion
        ($i:ident $n:ident $($rest_i:ident $rest_n:ident)* => $prev_i:ident $($prev_n:ident),*) => {
            for ($i, $n) in nodes.iter().enumerate().skip($prev_i + 1) {
                if [ $($prev_n),* ].iter().any(|&n| !graph.has_edge(n, $n)) {
                    continue;
                }

                wtf!($($rest_i $rest_n)* => $i $n, $($prev_n),*);
            }
        };
    }
    
    wtf!(
        i0 n0
        i1 n1
        i2 n2
        i3 n3
        i4 n4
        i5 n5
        i6 n6
        i7 n7
        i8 n8
        i9 n9
        i10 n10
        i11 n11
        i12 n12
    );

    unreachable!("No solution");
}
```

That... was certainly a macro.

```bash
$ cargo aoc --day 23 --part 2

AOC 2024
Day 23 - Part 2 - sorted_complete : di,gs,jw,kz,md,nc,qp,rp,sa,ss,uk,xk,yn
	generator: 16.666µs,
	runner: 9.681875ms

Day 23 - Part 2 - most_connected : di,gs,jw,kz,md,nc,qp,rp,sa,ss,uk,xk,yn
	generator: 17.666µs,
	runner: 3.456209ms

Day 23 - Part 2 - nested_loops : di,gs,jw,kz,md,nc,qp,rp,sa,ss,uk,xk,yn
	generator: 1.084µs,
	runner: 167.462333ms

Day 23 - Part 2 - nested_loops_macro : di,gs,jw,kz,md,nc,qp,rp,sa,ss,uk,xk,yn
	generator: 1.542µs,
	runner: 263.257291ms
```

And kind of hilarious. 

## Benchmarks

Anyways. 

```bash
$ cargo aoc bench --day 23

Day23 - Part1/v1                    time:   [20.133 ms 20.535 ms 21.110 ms]

Day23 - Part2/sorted_complete       time:   [4.5812 ms 4.6292 ms 4.6934 ms]
Day23 - Part2/most_connected        time:   [650.01 µs 662.88 µs 681.55 µs]
Day23 - Part2/nested_loops          time:   [181.16 ms 182.90 ms 184.81 ms]
Day23 - Part2/nested_loops_macro    time:   [291.93 ms 293.87 ms 295.91 ms]
```