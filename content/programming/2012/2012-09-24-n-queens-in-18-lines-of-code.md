---
title: n-queens in 18 lines of code
date: 2012-09-24 14:00:23
programming/languages:
- Scheme
programming/topics:
- Backtracking
- Mathematics
---
One of the rites of passage for computer scientists it seems is to solve the [[wiki:N-queens|Eight Queens Problem]]()--where you must place 8 queens on a chessboard so that no pair of queens is attacking each other. Even better is when you can expand that to the n-queens problem with n queens on an n by n chessboard. After finding it again in older posts on both <a href="http://programmingpraxis.com/2010/06/11/n-queens/" title="Programming Praxis: N-Queens">Programming Praxis</a> and <a href="http://www.datagenetics.com/blog/august42012/index.html" title="DataGenetics: Eight Queens">DataGenetics</a>, I decided to go ahead and take a crack at it and I think the solution is pretty straight forward.

<!--more-->

The most boring obvious solution would be to simply try every possible solution. For an 8x8 board, that turns out to be {{< inline-latex "\binom{8*8}{8} \approx 4.4e9" >}} or 4.4 billion. That's a fair few, but still entirely doable without too much effort. You can do a little better by restricting the solutions to exactly one queen per row and column. That reduces the number of necessary combinations all of the way down to {{< inline-latex "8! = 40,320" >}} combinations. Much better, but it still seems like we should be able to do better.

Finally, we're at the solution hat I actually used: a simple backtracking model. Start by placing a queen in the first row and column. Then, for each row after that, place a queen in the first column that is available. If you ever get into a position where that just isn't possible, back up through the decisions you made, undoing them one at a time and trying the next column instead. Eventually, you might get all the way back to that original first row and column choice if it's not possible to place a queen in the corner and still solve the problem (that's not actually true, there are actually four such solutions for an 8x8 board).

For this particular algorithm, Scheme is a natural choice as the backtracking algorithm is a direct analogue to recursion. You can use the nested function calls to keep track of how far you have to back up, which makes it rather nice. For this particular implementation, the goal is to return all valid solutions as a list of row,column points.

In any case, here's my code:

```scheme
(define (queens n)
  (let loop ([queens '()] [row 0] [col 0])
    (cond
      [(= row n) (list queens)]
      [(= col n) '()]
      [else
       (let ([new-queen (list row col)])
         (if (any? (lambda (old-queen)
                     (or (= (car old-queen) (car new-queen))
                         (= (cadr old-queen) (cadr new-queen))
                         (= 1 (abs (/ (- (cadr old-queen) (cadr new-queen))
                                      (- (car old-queen) (car new-queen)))))))
               queens)
             (loop queens row (+ col 1))
             (append
               (loop (cons new-queen queens) (+ row 1) 0)
               (loop queens row (+ col 1)))))])))

(define (any? ? l) (not (null? (filter ? l))))
```

Simple enough, although there are a few potential gotchas:

```scheme
[(= row n) (list queens)]
[(= col n) '()]
```

The first two `cond` cases are for running off the edges. If you've run off the last row that means you've successfully placed a queen in every row of the board so you should return the list of queens thus far. It's wrapped in another call to `list` as the expected solution is a list of solutions, not just a single solution. The second case is for running off of a column. If you get here, that means that you've tried every solution in this particular row and either branched to look for more valid solutions or you're done and there aren't any. In either case, you just want an empty set of solutions for this branch.

```scheme
(any? (lambda (old-queen)
        (or (= (car old-queen) (car new-queen))
            (= (cadr old-queen) (cadr new-queen))
            (= 1 (abs (/ (- (cadr old-queen) (cadr new-queen))
                         (- (car old-queen) (car new-queen)))))))
  queens)
```

The next interesting bit of code uses the `any?` function I've shown several times before to ask if there is any `old-queen` in `queens` that is in the same row, column, or diagonal (respectively) as the `new-queen` that we're trying to place. I'll admit that the code is a bit messy here and it was originally factored out into three helper functions, but since they're only used once, I went ahead and inlined them.

The rest is just the branching possibilities. If the `any?` returns `#t`, that means there is already a queen that can attack this square so just try the next column. If it doesn't return `#t` though, that means that we could place a queen here. So what we do is branch by first checking for any solutions starting in the next row that have the new queen in them and then checking for any solutions still in this row without the new queen. Stick the two lists together and we have our overall solution. Recursion is awesome.

Here is an example run showing the 10 solutions to the 5-queens problem:

```
~ (queens 5)
 (((4 3) (3 1) (2 4) (1 2) (0 0))
  ((4 2) (3 4) (2 1) (1 3) (0 0))
  ((4 4) (3 2) (2 0) (1 3) (0 1))
  ((4 3) (3 0) (2 2) (1 4) (0 1))
  ((4 4) (3 1) (2 3) (1 0) (0 2))
  ((4 0) (3 3) (2 1) (1 4) (0 2))
  ((4 1) (3 4) (2 2) (1 0) (0 3))
  ((4 0) (3 2) (2 4) (1 1) (0 3))
  ((4 2) (3 0) (2 3) (1 1) (0 4))
  ((4 1) (3 3) (2 0) (1 2) (0 4)))
```

Also, for those interested, I ran my code against the first several values for n:

| n  | solutions | time (sec) |
|----|-----------|------------|
| 1  |     1     |     0      |
| 2  |     0     |     0      |
| 3  |     0     |     0      |
| 4  |     2     |     0      |
| 5  |    10     |     0      |
| 6  |     4     |   0.001    |
| 7  |    40     |   0.003    |
| 8  |    92     |   0.019    |
| 9  |    352    |   0.102    |
| 10 |    724    |   0.549    |
| 11 |   2680    |   3.031    |
| 12 |   14200   |   19.282   |
| 13 |   73712   |  132.300   |


All in all, a fun little problem. I'm tempted to try for some of the more interesting possible algorithms for this at some point. For example I was toying with the idea of using a genetic algorithm to solve it, although I have a feeling that there is too much repetitiveness and symmetry to the solution space for that to be an effective method. Still, it could be interesting.

If you'd like, you can download the source here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/n-queens.ss" title="n-queens source code">n queens source</a>
