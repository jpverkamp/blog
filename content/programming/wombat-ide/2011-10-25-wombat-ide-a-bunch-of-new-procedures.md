---
title: Wombat IDE - A bunch of new procedures
date: 2011-10-25 04:55:10
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
I've added a bunch of new procedures today, mostly to improve compatibility with Chez Scheme and the like. All together, I've added these functions:

* `cpu-time` - get a timestamp to use in timing function runtime


<!--more-->

```scheme
~ (cpu-time)
1.339726427264E9

~ (let ([start (cpu-time)])
    (long-running-function)
    (- (cpu-time) start))
0.7339999675750732
```


* `filter` - keep only elements that match a given predicate


```scheme
~ (filter even? '(8 6 7 5 3 0 9))
(8 6 0)
```


* `[[wiki:Fold (higher-order function)|fold-left]]()` - perform formulaic recursive procedures on lists from, see the linked Wikipedia article for more details


```scheme
~ (fold-left cons '() '(8 6 7 5 3 0 9))
(((((((() . 8) . 6) . 7) . 5) . 3) . 0) . 9)

~ (fold-left + 0 '(8 6 7 5 3 0 9))
38
```


* `[[wiki:Fold (higher-order function)|fold-right]]()` - similar to `fold-left` with the arguments reversed


```scheme
~ (fold-right cons '() '(8 6 7 5 3 0 9))
(8 6 7 5 3 0 9)

~ (fold-right + 0 '(8 6 7 5 3 0 9))
38
```


* `any?` - tests if any item in a list matches a given predicate


```scheme
~ (any? even? '(8 6 7 5 3 0 9))
#t
```


* `all?` - tests if all items in a list match a given predicate


```scheme
~ (all? even? '(8 6 7 5 3 0 9))
#f
```

Hopefully at least some of these will be useful. The current version is <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">1.297.15</a>.